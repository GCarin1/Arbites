"""Critérios de aceite da spec profile (SC14) — memória injetada na IA."""

import json as jsonlib

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

GENERATED = {"testcases": [{"title": "X", "passos": ["p"], "resultado_esperado": "ok"}]}


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


class RecordingTransport(httpx.MockTransport):
    """Grava o payload enviado ao provider para inspecionar o prompt."""

    def __init__(self, content: str):
        self.requests: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(jsonlib.loads(request.content))
            return httpx.Response(
                200, json={"choices": [{"message": {"content": content}}]}
            )

        super().__init__(handler)


@pytest.fixture()
def rig(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [{"name": "local", "kind": "lmstudio", "model": "x"}],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    transport = RecordingTransport(jsonlib.dumps(GENERATED, ensure_ascii=False))
    app = create_app(ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
                     ai_transport=transport, github_client=object())
    with TestClient(app) as c:
        c.ws = ws
        yield c, transport


def test_profile_template_and_roundtrip(rig):
    client, _ = rig
    prof = client.get("/api/v1/profile").json()
    assert "Preferências & Estilo" in prof["memory"]
    assert "Contexto Ativo" in prof["memory"]
    assert (client.ws.root / "profile.md").exists()

    saved = client.put(
        "/api/v1/profile",
        json={"name": "Carini", "memory": "## Preferências & Estilo\n\n- Direto ao ponto\n"},
    ).json()
    assert saved["name"] == "Carini"
    again = client.get("/api/v1/profile").json()
    assert again["name"] == "Carini" and "Direto ao ponto" in again["memory"]


def test_memory_injected_into_ai_prompt(rig):
    client, transport = rig
    client.put(
        "/api/v1/profile",
        json={"memory": "## Contexto Ativo\n\n- Projeto Arbites, squad pagamentos\n"},
    )
    resp = client.post(
        "/api/v1/ai/generate-testcases", json={"source": "story de login"}
    )
    assert resp.status_code == 200
    sent = transport.requests[-1]
    user_msg = sent["messages"][-1]["content"]
    assert "memória de longo prazo" in user_msg
    assert "squad pagamentos" in user_msg
    assert "story de login" in user_msg


def test_empty_or_template_memory_adds_no_context_block(rig):
    client, transport = rig
    client.get("/api/v1/profile")  # cria com template intocado
    client.post("/api/v1/ai/generate-testcases", json={"source": "story x"})
    user_msg = transport.requests[-1]["messages"][-1]["content"]
    assert "memória de longo prazo" not in user_msg
    assert user_msg.startswith("story x")
