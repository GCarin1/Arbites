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
    assert {s["name"] for s in switches} == set(auth_ops.SWITCHES)
    assert all(s["enabled"] for s in switches)
    assert all(s["updated_at"] is None for s in switches)


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
    assert len(response.json()["switches"]) == len(auth_ops.SWITCHES)
