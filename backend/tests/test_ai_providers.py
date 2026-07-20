"""Testar provider de IA (0085) — POST /ai/providers/test faz uma chamada
mínima e devolve {ok, error}, sem gravar nada. MockTransport httpx."""

import httpx
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


def _transport():
    """200 só quando a chave é 'sk-valid'; senão 401 (chave inválida)."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("authorization") == "Bearer sk-valid":
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "ok"}}]}
            )
        return httpx.Response(401, json={"error": "invalid api key"})

    return httpx.MockTransport(handler)


def _client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "cloud",
        "providers": [
            {"name": "cloud", "kind": "openai_compatible",
             "base_url": "https://api.example.com/v1", "model": "gpt"},
        ],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    keys = FakeAIKeyStore()
    keys.set("cloud", "sk-valid")
    app = create_app(ws.root, watch=False, ai_key_store=keys,
                     ai_transport=_transport(), github_client=object())
    c = TestClient(app)
    c.ws = ws
    return c


def test_saved_provider_with_valid_key_is_ok(tmp_path):
    with _client(tmp_path) as c:
        r = c.post("/api/v1/ai/providers/test", json={"name": "cloud"})
        assert r.status_code == 200
        assert r.json() == {"ok": True, "error": None}


def test_inline_provider_invalid_key_reports_error(tmp_path):
    with _client(tmp_path) as c:
        r = c.post("/api/v1/ai/providers/test", json={
            "kind": "openai_compatible", "model": "gpt",
            "base_url": "https://api.example.com/v1", "key": "sk-bad",
        })
        body = r.json()
        assert body["ok"] is False
        assert "401" in body["error"]


def test_inline_provider_valid_key_is_ok(tmp_path):
    with _client(tmp_path) as c:
        r = c.post("/api/v1/ai/providers/test", json={
            "kind": "openai_compatible", "model": "gpt",
            "base_url": "https://api.example.com/v1", "key": "sk-valid",
        })
        assert r.json()["ok"] is True


def test_test_without_name_or_kind_is_422(tmp_path):
    with _client(tmp_path) as c:
        r = c.post("/api/v1/ai/providers/test", json={})
        assert r.status_code == 422


def test_unknown_saved_provider_is_404(tmp_path):
    with _client(tmp_path) as c:
        r = c.post("/api/v1/ai/providers/test", json={"name": "nope"})
        assert r.status_code == 404
