"""Importação inteligente via IA (doc §1.1) — txt/md/xml livre → BDD preview."""

import json

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

CONVERSION = {
    "folder": "login",
    "testcases": [
        {
            "title": "Login com credenciais válidas",
            "pre_condicoes": ["usuário cadastrado"],
            "passos": ["abrir a tela de login", "informar credenciais"],
            "resultado_esperado": "dashboard exibido",
        }
    ],
}


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


@pytest.fixture()
def client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [{"name": "local", "kind": "lmstudio", "model": "gemma-2-9b"}],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(CONVERSION, ensure_ascii=False)}}]},
        )
    )
    app = create_app(ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
                     ai_transport=transport, github_client=object())
    with TestClient(app) as c:
        c.ws = ws
        yield c


def test_import_ai_converts_free_text_to_bdd_preview(client):
    resp = client.post(
        "/api/v1/import/ai",
        files={"file": ("casos_login.txt", "1) login ok: abrir tela...", "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["preview"] is True and data["folder"] == "login"
    body = data["testcases"][0]["body"]
    assert "Scenario: Login com credenciais válidas" in body
    assert "Given usuário cadastrado" in body
    assert "When abrir a tela de login" in body
    assert "Then dashboard exibido" in body
    # nada gravado sem aceite
    assert client.get("/api/v1/testcases").json() == []

    # aceite = POST /testcases normal, na pasta sugerida
    ct = client.post(
        "/api/v1/testcases",
        json={"title": data["testcases"][0]["title"], "folder": data["folder"],
              "body": body},
    ).json()
    assert ct["path"].startswith("testcases/login/")


def test_import_ai_rejects_unsupported_extension_and_empty(client):
    resp = client.post(
        "/api/v1/import/ai", files={"file": ("casos.pdf", b"%PDF", "application/pdf")}
    )
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "invalid_file"
    resp2 = client.post(
        "/api/v1/import/ai", files={"file": ("vazio.txt", "", "text/plain")}
    )
    assert resp2.status_code == 422 and resp2.json()["error"]["code"] == "empty_file"
