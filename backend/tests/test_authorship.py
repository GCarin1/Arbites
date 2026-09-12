"""Testes de autoria e perfil por conta — acceptance criteria do 0104."""

import frontmatter

from arbites import auth as auth_ops
from conftest import ADMIN_EMAIL, login_admin

OTHER = {"email": "outra@arbites.test", "password": "senha-da-outra-1"}


def _become(test_client, credentials, role="editor"):
    conn = test_client.app.state.auth
    if auth_ops.get_user_by_email(conn, credentials["email"]) is None:
        auth_ops.create_user(conn, credentials["email"], credentials["password"],
                             role=role, status="active")
    test_client.post("/api/v1/auth/logout")
    response = test_client.post("/api/v1/auth/login", json={
        "email": credentials["email"], "password": credentials["password"]})
    assert response.status_code == 200, response.text


def _meta(ws, relative_glob, entity_id):
    for path in (ws.root / relative_glob).glob("*.md"):
        post = frontmatter.load(str(path))
        if post.metadata.get("id") == entity_id:
            return post.metadata
    raise AssertionError(f"{entity_id} não encontrado em {relative_glob}")


# -- AC1: cada conta lê e injeta a própria memória ---------------------------


def test_cada_conta_le_apenas_o_proprio_perfil(anon_client):
    login_admin(anon_client)
    anon_client.put("/api/v1/profile",
                    json={"name": "Admin", "memory": "## Contexto Ativo\n\nsquad alfa\n"})

    _become(anon_client, OTHER)
    mine = anon_client.get("/api/v1/profile").json()
    assert "squad alfa" not in mine["memory"]
    assert mine["name"] == ""
    anon_client.put("/api/v1/profile",
                    json={"name": "Outra", "memory": "## Contexto Ativo\n\nsquad beta\n"})

    login_admin(anon_client)
    assert "squad alfa" in anon_client.get("/api/v1/profile").json()["memory"]
    assert "squad beta" not in anon_client.get("/api/v1/profile").json()["memory"]


def test_o_perfil_de_cada_conta_e_um_arquivo_proprio(client, ws):
    client.put("/api/v1/profile", json={"memory": "## Contexto Ativo\n\nminha nota\n"})
    files = list((ws.root / "profiles").glob("*.md"))
    assert len(files) == 1
    assert "minha nota" in files[0].read_text(encoding="utf-8")


# -- AC2: owner da execution vem da sessão -----------------------------------


def test_owner_da_execution_e_a_sessao_e_ignora_o_corpo(anon_client):
    _become(anon_client, OTHER)
    created = anon_client.post("/api/v1/testcases", json={"title": "Login"}).json()
    execution = anon_client.post("/api/v1/executions", json={
        "name": "Regressão", "testcase_ids": [created["id"]],
        # Um cliente mal-intencionado assinando com o nome de outro:
        "owner": "chefe@arbites.test",
    }).json()
    assert execution["owner"] == OTHER["email"]


# -- AC3: created_by no frontmatter, preservado nas edições ------------------


def test_artefatos_nascem_com_created_by(anon_client, ws):
    _become(anon_client, OTHER)
    story = anon_client.post("/api/v1/requirements",
                             json={"kind": "story", "title": "Login"}).json()
    testcase = anon_client.post("/api/v1/testcases",
                                json={"title": "Login válido"}).json()
    defect = anon_client.post("/api/v1/defects",
                              json={"title": "Botão sumiu"}).json()

    assert _meta(ws, "requirements", story["id"])["created_by"] == OTHER["email"]
    assert _meta(ws, "testcases", testcase["id"])["created_by"] == OTHER["email"]
    assert _meta(ws, "defects", defect["id"])["created_by"] == OTHER["email"]


def test_editar_nao_troca_quem_criou(anon_client, ws):
    _become(anon_client, OTHER)
    testcase = anon_client.post("/api/v1/testcases",
                                json={"title": "Login válido"}).json()

    # Outra pessoa edita: quem criou não muda, porque criar aconteceu uma vez.
    login_admin(anon_client)
    anon_client.put(f"/api/v1/testcases/{testcase['id']}",
                    json={"title": "Login válido (revisado)"})
    assert _meta(ws, "testcases", testcase["id"])["created_by"] == OTHER["email"]


# -- AC4: herança única do profile.md da raiz --------------------------------


def test_a_conta_de_menor_id_herda_o_profile_da_raiz_uma_vez(anon_client, ws):
    legado = "## Contexto Ativo\n\nmemória escrita antes do multiusuário\n"
    (ws.root / "profile.md").write_text(
        f"---\nname: Antigo\n---\n\n{legado}", encoding="utf-8")

    # O admin de bootstrap é a conta de menor id.
    login_admin(anon_client)
    inherited = anon_client.get("/api/v1/profile").json()
    assert "antes do multiusuário" in inherited["memory"]
    assert inherited["name"] == "Antigo"
    # Herdado uma vez: o arquivo da raiz sai de cena.
    assert not (ws.root / "profile.md").exists()

    # A segunda conta começa do template, sem enxergar a memória da primeira.
    _become(anon_client, OTHER)
    fresh = anon_client.get("/api/v1/profile").json()
    assert "antes do multiusuário" not in fresh["memory"]
    assert "Preferências & Estilo" in fresh["memory"]


def test_sem_profile_legado_a_primeira_conta_comeca_do_template(client):
    profile = client.get("/api/v1/profile").json()
    assert "Preferências & Estilo" in profile["memory"]
    assert "Contexto Ativo" in profile["memory"]


# -- AC5: instalação de uma pessoa só não muda de comportamento --------------


def test_com_auth_off_o_perfil_e_a_raiz_e_a_autoria_e_local(ws, monkeypatch):
    from fastapi.testclient import TestClient

    from arbites.api import create_app

    monkeypatch.setenv("ARBITES_AUTH", "off")
    with TestClient(create_app(ws.root, watch=False)) as local:
        local.put("/api/v1/profile", json={"memory": "## Contexto Ativo\n\nsó eu\n"})
        assert (ws.root / "profile.md").exists()
        assert not (ws.root / "profiles").exists()

        created = local.post("/api/v1/testcases", json={"title": "Login"}).json()
        assert _meta(ws, "testcases", created["id"])["created_by"] == "local"
        execution = local.post("/api/v1/executions", json={
            "name": "Regressão", "testcase_ids": [created["id"]]}).json()
        assert execution["owner"] == "local"


def test_a_memoria_injetada_na_ia_e_a_de_quem_chamou(ws, monkeypatch):
    """A memória entra em toda chamada de IA: se vazasse entre contas, a IA
    responderia a um QA com o contexto de outro."""
    import json as jsonlib

    import httpx
    from fastapi.testclient import TestClient

    from arbites.api import create_app
    from arbites.workspace import DEFAULT_CONFIG

    import yaml

    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [{"name": "local", "kind": "openai_compatible",
                       "base_url": "http://localhost:1234/v1", "model": "x"}],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")

    sent: list = []
    payload = {"testcases": [{"title": "t", "steps": [], "priority": "medium"}]}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(jsonlib.loads(request.content))
        return httpx.Response(200, json={
            "choices": [{"message": {
                "content": jsonlib.dumps(payload, ensure_ascii=False)}}]})

    class Keys:
        def get(self, name):
            return "k"

        def set(self, name, value):
            pass

        def status(self):
            return {}

    monkeypatch.setenv("ARBITES_ADMIN_EMAIL", ADMIN_EMAIL)
    with TestClient(create_app(
        ws.root, watch=False, ai_key_store=Keys(), github_client=object(),
        ai_transport=httpx.MockTransport(handler),
    )) as app_client:
        login_admin(app_client)
        app_client.put("/api/v1/profile",
                       json={"memory": "## Contexto Ativo\n\nsegredo do admin\n"})
        _become(app_client, OTHER)
        app_client.put("/api/v1/profile",
                       json={"memory": "## Contexto Ativo\n\nsegredo da outra\n"})

        app_client.post("/api/v1/ai/generate-testcases", json={"source": "story x"})
        prompt = sent[-1]["messages"][-1]["content"]
        assert "segredo da outra" in prompt
        assert "segredo do admin" not in prompt
