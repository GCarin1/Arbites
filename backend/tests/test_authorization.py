"""Testes de autorização e interruptores — acceptance criteria do 0101."""

import pytest

from arbites import auth as auth_ops
from conftest import ADMIN_EMAIL, login_admin

VIEWER = {"email": "viewer@arbites.test", "password": "senha-de-viewer-1"}
EDITOR = {"email": "editor@arbites.test", "password": "senha-de-editor-1"}


def _make(test_client, credentials, role):
    """Cria uma conta já ativa com o papel pedido e devolve o login pronto."""
    conn = test_client.app.state.auth
    auth_ops.create_user(
        conn, credentials["email"], credentials["password"],
        role=role, status="active",
    )
    return credentials


def _login(test_client, credentials):
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert response.status_code == 200, response.text


@pytest.fixture()
def viewer(anon_client):
    _make(anon_client, VIEWER, "viewer")
    _login(anon_client, VIEWER)
    return anon_client


@pytest.fixture()
def editor(anon_client):
    _make(anon_client, EDITOR, "editor")
    _login(anon_client, EDITOR)
    return anon_client


# -- AC1: viewer lê tudo e não escreve nada ---------------------------------


def test_viewer_le_por_get(viewer):
    assert viewer.get("/api/v1/workspace").status_code == 200
    assert viewer.get("/api/v1/testcases").status_code == 200
    assert viewer.get("/api/v1/requirements").status_code == 200


def test_viewer_nao_escreve_em_nenhuma_rota_de_escrita(viewer):
    """Varre as rotas registradas em vez de manter uma lista à mão: uma rota
    de escrita nova entra nesta prova sozinha."""
    checked = 0
    for route in viewer.app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set()) or set()
        if not path.startswith("/api/v1") or path.startswith("/api/v1/auth"):
            continue
        writes = methods - {"GET", "HEAD", "OPTIONS"}
        if not writes:
            continue
        # Placeholders viram um valor qualquer: a recusa acontece antes de a
        # rota olhar para o argumento.
        concrete = path
        while "{" in concrete:
            start = concrete.index("{")
            end = concrete.index("}", start)
            concrete = concrete[:start] + "x" + concrete[end + 1:]
        for method in sorted(writes):
            response = viewer.request(method, concrete, json={})
            assert response.status_code == 403, (
                "%s %s deveria recusar viewer, respondeu %s"
                % (method, concrete, response.status_code)
            )
            assert response.json()["error"]["code"] == "forbidden"
            checked += 1
    assert checked > 20, "a varredura precisa cobrir a API real, cobriu %d" % checked


def test_viewer_troca_a_propria_senha(viewer):
    response = viewer.post(
        "/api/v1/auth/password",
        json={"current_password": VIEWER["password"],
              "new_password": "nova-senha-viewer-1"},
    )
    assert response.status_code == 200


# -- AC2: editor trabalha, mas não administra -------------------------------


def test_editor_cria_artefatos(editor):
    created = editor.post(
        "/api/v1/testcases", json={"title": "Login válido"}
    )
    assert created.status_code == 201
    story = editor.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Login"}
    )
    assert story.status_code == 201


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("PUT", "/api/v1/targets", {"targets": []}),
        ("PUT", "/api/v1/settings/github/token", {"token": "ghp_x"}),
        ("PUT", "/api/v1/ai/providers", {"providers": []}),
        ("PUT", "/api/v1/admin/switches/local_runner", {"enabled": False}),
    ],
)
def test_editor_nao_alcanca_superficie_governada(editor, method, path, body):
    response = editor.request(method, path, json=body)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


@pytest.mark.parametrize(
    "path",
    ["/api/v1/automation/browse-features", "/api/v1/env/catalog",
     "/api/v1/targets/qualquer/env"],
)
def test_editor_nao_le_superficie_governada(editor, path):
    response = editor.get(path)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_put_targets_e_privativo_do_admin(editor):
    """PUT /targets define python_path e working_dir do subprocess: e o
    caminho real para executar codigo no servidor."""
    refused = editor.put("/api/v1/targets", json={
        "targets": [{"name": "x", "local_path": "/tmp",
                     "python_path": "/bin/sh"}],
    })
    assert refused.status_code == 403


# -- AC3 e AC4: interruptores -----------------------------------------------


def test_interruptores_nascem_todos_ligados(client):
    switches = client.get("/api/v1/admin/switches").json()["switches"]
    # Duas famílias na mesma lista (ADR 0014): superfície perigosa governa
    # uma CAPACIDADE técnica, módulo governa uma TELA e os caminhos dela.
    assert {s["name"] for s in switches} == set(auth_ops.SWITCHES) | set(
        auth_ops.MODULES
    )
    assert all(s["enabled"] for s in switches)
    assert all(s["updated_at"] is None for s in switches)
    por_nome = {s["name"]: s for s in switches}
    assert por_nome["ai"]["kind"] == "surface"
    assert por_nome["ai"]["tab"] is None
    assert por_nome["mod_ia"]["kind"] == "module"
    assert por_nome["mod_ia"]["tab"] == "ia"


def test_desligar_local_runner_recusa_a_rota_e_religar_devolve(client):
    off = client.put("/api/v1/admin/switches/local_runner",
                     json={"enabled": False})
    assert off.status_code == 200
    assert off.json()["switch"]["enabled"] is False
    assert off.json()["switch"]["updated_by"] == ADMIN_EMAIL

    refused = client.post("/api/v1/runs/local",
                          json={"target": "x", "testcase_ids": ["CT-1"]})
    assert refused.status_code == 403
    body = refused.json()["error"]
    assert body["code"] == "feature_disabled"
    assert "local_runner" in body["message"]

    # Religar vale na hora, sem reiniciar o processo.
    client.put("/api/v1/admin/switches/local_runner", json={"enabled": True})
    again = client.post("/api/v1/runs/local",
                        json={"target": "x", "testcase_ids": ["CT-1"]})
    assert again.status_code != 403


def test_desligar_ai_recusa_toda_rota_de_ia(client):
    client.put("/api/v1/admin/switches/ai", json={"enabled": False})
    for path, body in [
        ("/api/v1/ai/generate-testcases", {"source": "story x"}),
        ("/api/v1/ai/executive-summary", {}),
    ]:
        response = client.post(path, json=body)
        assert response.status_code == 403, path
        assert response.json()["error"]["code"] == "feature_disabled"


def test_desligar_filesystem_browse_e_target_env(client):
    client.put("/api/v1/admin/switches/filesystem_browse",
               json={"enabled": False})
    client.put("/api/v1/admin/switches/target_env", json={"enabled": False})
    assert client.get(
        "/api/v1/automation/browse-features"
    ).json()["error"]["code"] == "feature_disabled"
    assert client.get("/api/v1/env/catalog").json()["error"]["code"] == "feature_disabled"


def test_interruptor_sobrevive_ao_reinicio_do_processo(ws, client):
    from fastapi.testclient import TestClient

    from arbites.api import create_app

    client.put("/api/v1/admin/switches/xray_import", json={"enabled": False})

    # Novo processo sobre o mesmo workspace: o estado vem do banco duravel.
    with TestClient(create_app(ws.root, watch=False)) as restarted:
        login_admin(restarted)
        switches = {
            s["name"]: s["enabled"]
            for s in restarted.get("/api/v1/admin/switches").json()["switches"]
        }
        assert switches["xray_import"] is False
        assert switches["local_runner"] is True


def test_interruptor_desconhecido_e_404(client):
    response = client.put("/api/v1/admin/switches/inexistente",
                          json={"enabled": False})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_switch"


def test_estado_dos_interruptores_e_legivel_por_qualquer_sessao(viewer):
    """A UI precisa esconder o que esta desligado; o estado nao e segredo."""
    response = viewer.get("/api/v1/admin/switches")
    assert response.status_code == 200
    assert len(response.json()["switches"]) == len(auth_ops.SWITCHES) + len(
        auth_ops.MODULES
    )


# -- módulos desligáveis (ADR 0014, change 0143) ----------------------------


def test_modulo_desligado_recusa_todos_os_seus_caminhos(client):
    """Desligar um módulo desliga a FEATURE, não só o item do menu.

    Antes, o interruptor de superfície escondia a aba em alguns casos e nunca
    bloqueava a rota do cliente: quem tivesse o link na mão abria a tela
    inteira e só descobria no primeiro envio. O backend é a única camada que
    vale como segurança, e é ela que este teste prende.
    """
    assert client.get("/api/v1/decisions").status_code == 200

    off = client.put("/api/v1/admin/switches/mod_decisions", json={"enabled": False})
    assert off.status_code == 200
    assert off.json()["switch"]["enabled"] is False

    recusa = client.get("/api/v1/decisions")
    assert recusa.status_code == 403
    assert recusa.json()["error"]["code"] == "feature_disabled"
    # a escrita também, não só a leitura
    assert client.post("/api/v1/decisions", json={"title": "x"}).status_code == 403

    # religar vale na hora, sem reiniciar o processo
    client.put("/api/v1/admin/switches/mod_decisions", json={"enabled": True})
    assert client.get("/api/v1/decisions").status_code == 200


def test_modulo_desligado_nao_derruba_o_resto_do_produto(client):
    """O interruptor é cirúrgico: o núcleo não pode cair junto."""
    client.put("/api/v1/admin/switches/mod_meetings", json={"enabled": False})
    assert client.get("/api/v1/meetings").status_code == 403
    for rota in ("/api/v1/requirements", "/api/v1/testcases", "/api/v1/executions",
                 "/api/v1/defects", "/api/v1/todos"):
        assert client.get(rota).status_code == 200, rota


def test_cada_modulo_conhecido_tem_aba_e_caminhos(client):
    """Registro sem aba ou sem caminho é um interruptor que não desliga nada."""
    for name, spec in auth_ops.MODULES.items():
        assert spec["tab"], name
        assert spec["paths"], name
        assert all(p.startswith("/") for p in spec["paths"]), name


def test_so_admin_liga_e_desliga_interruptor(viewer, editor):
    """Quem não é admin não mexe em interruptor — nem módulo, nem superfície."""
    for sessao in (viewer, editor):
        for name in ("mod_ia", "ai"):
            negado = sessao.put(
                "/api/v1/admin/switches/%s" % name, json={"enabled": False}
            )
            assert negado.status_code == 403, (name, negado.text)


def test_so_admin_alcanca_a_gestao_de_contas(viewer, editor):
    """Liberar, recusar, desativar e reativar cadastro são do admin e só dele."""
    for sessao in (viewer, editor):
        assert sessao.get("/api/v1/admin/users").status_code == 403
        assert sessao.post("/api/v1/admin/users/1/approve",
                           json={"role": "viewer"}).status_code == 403
        assert sessao.post("/api/v1/admin/users/1/reject").status_code == 403
        assert sessao.post("/api/v1/admin/users/1/disable").status_code == 403
        assert sessao.post("/api/v1/admin/users/1/enable").status_code == 403


def test_so_admin_exclui_rodada_de_auditoria(viewer, editor):
    """Rodar e ler auditoria é de todos; apagar é de quem administra (0151).

    Uma rodada é o retrato do estado de qualidade num momento — apagar é
    mais perto de destruir registro do que de descartar rascunho.
    """
    for sessao in (viewer, editor):
        # ler continua aberto
        assert sessao.get("/api/v1/audit/history").status_code == 200
        # apagar, não
        assert sessao.delete("/api/v1/audit/AUD-0001").status_code == 403
        assert sessao.request(
            "DELETE", "/api/v1/audit?before=2030-01-01T00:00:00+00:00"
        ).status_code == 403
