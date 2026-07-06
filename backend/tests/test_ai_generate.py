"""Critérios de aceite da spec ai-assist (SC7) — MockTransport httpx.

Dois caminhos de provider: OpenAI-compatível (o caso LM Studio local) e
Anthropic (o caso cloud). O gate não chama LLM real; os shapes das APIs
ficam fixados aqui.
"""

import json

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

STORY_BODY = (
    "## Resumo\n\nComo usuário cadastrado, quero autenticar com e-mail e senha.\n\n"
    "## Critérios de aceite\n\n"
    "- WHEN credenciais válidas THEN exibe o dashboard.\n"
    "- WHEN senha inválida THEN erro sem revelar o campo.\n"
)

GENERATED = {
    "testcases": [
        {
            "title": "Login com credenciais válidas",
            "type": "manual",
            "priority": "high",
            "tags": ["login", "smoke"],
            "objetivo": "Validar autenticação com credenciais corretas.",
            "pre_condicoes": ["Usuário ativo cadastrado"],
            "passos": ["Abrir a tela de login", "Informar credenciais válidas",
                       "Clicar em Entrar"],
            "resultado_esperado": "Dashboard exibido com o nome do usuário.",
        },
        {
            "title": "Login com senha inválida",
            "type": "manual",
            "priority": "medium",
            "tags": ["login"],
            "objetivo": "Validar mensagem de erro.",
            "pre_condicoes": [],
            "passos": ["Abrir a tela de login", "Informar senha inválida"],
            "resultado_esperado": "Erro exibido sem revelar qual campo errou.",
        },
    ]
}


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


def _transport(content: str):
    """Responde no shape certo conforme a URL (OpenAI-compat vs Anthropic)."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "anthropic.com" in request.url.host:
            return httpx.Response(
                200, json={"content": [{"type": "text", "text": content}]}
            )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": content}}]},
        )

    return httpx.MockTransport(handler)


def _make_client(tmp_path, content: str):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "lmstudio-local",
        "providers": [
            {"name": "lmstudio-local", "kind": "openai_compatible",
             "base_url": "http://localhost:1234/v1", "model": "qwen"},
            {"name": "anthropic-cloud", "kind": "anthropic",
             "model": "claude-sonnet-5"},
        ],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    keys = FakeAIKeyStore()
    keys.set("anthropic-cloud", "sk-ant-fake")
    app = create_app(ws.root, watch=False, ai_key_store=keys,
                     ai_transport=_transport(content), github_client=object())
    client = TestClient(app)
    client.ws = ws
    return client


@pytest.fixture()
def ai_client(tmp_path):
    with _make_client(tmp_path, json.dumps(GENERATED, ensure_ascii=False)) as client:
        yield client


def _story(client):
    return client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Login válido", "body": STORY_BODY},
    ).json()


def test_generate_from_story_with_local_and_cloud_provider(ai_client):
    story = _story(ai_client)
    for provider in ("lmstudio-local", "anthropic-cloud"):
        resp = ai_client.post(
            "/api/v1/ai/generate-testcases",
            json={"source": story["id"], "provider": provider},
        )
        assert resp.status_code == 200, resp.text
        preview = resp.json()
        assert preview["preview"] is True
        assert len(preview["testcases"]) == 2
        first = preview["testcases"][0]
        assert first["title"] == "Login com credenciais válidas"
        assert "## Passos" in first["body"] and "1. Abrir a tela de login" in first["body"]
    # preview NÃO grava nada
    ws = ai_client.ws
    assert not list((ws.root / "testcases").rglob("*.md"))


def test_accept_reject_item_by_item(ai_client):
    story = _story(ai_client)
    preview = ai_client.post(
        "/api/v1/ai/generate-testcases", json={"source": story["id"]}
    ).json()
    accepted, rejected = preview["testcases"][0], preview["testcases"][1]
    # aceite = POST /testcases com o conteúdo do item (o item rejeitado morre no preview)
    created = ai_client.post(
        "/api/v1/testcases",
        json={
            "title": accepted["title"],
            "priority": accepted["priority"],
            "tags": accepted["tags"],
            "story": story["id"],
            "body": accepted["body"],
        },
    ).json()
    ws = ai_client.ws
    files = list((ws.root / "testcases").rglob("*.md"))
    assert len(files) == 1  # só o aceito
    assert created["title"] == accepted["title"]
    assert rejected["title"] not in files[0].read_text(encoding="utf-8")


def test_output_outside_schema_is_rejected_without_writes(tmp_path):
    bad = json.dumps({"testcases": [{"title": "sem passos"}]})  # falta campo obrigatório
    with _make_client(tmp_path, bad) as client:
        story = client.post(
            "/api/v1/requirements",
            json={"kind": "story", "title": "S", "body": STORY_BODY},
        ).json()
        resp = client.post(
            "/api/v1/ai/generate-testcases", json={"source": story["id"]}
        )
        assert resp.status_code == 422
        error = resp.json()["error"]
        assert error["code"] == "schema_mismatch"
        assert "GeneratedTestcases" in error["message"]
        assert not list((client.ws.root / "testcases").rglob("*.md"))


def test_non_json_output_is_clear_error(tmp_path):
    with _make_client(tmp_path, "Desculpe, não posso ajudar com isso.") as client:
        story = client.post(
            "/api/v1/requirements",
            json={"kind": "story", "title": "S", "body": STORY_BODY},
        ).json()
        resp = client.post(
            "/api/v1/ai/generate-testcases", json={"source": story["id"]}
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "invalid_output"


def test_review_uses_index_candidates(ai_client):
    review_payload = {
        "issues": [
            {"kind": "duplicidade", "message": "Parece duplicar CT existente"},
            {"kind": "resultado_vago", "message": "Resultado esperado vago",
             "step_index": None},
        ],
        "summary": "2 achados",
    }
    # cria dois CTs com títulos similares para o índice sugerir candidato
    for title in ("Login com credenciais válidas", "Login com credenciais corretas"):
        ai_client.post(
            "/api/v1/testcases",
            json={"title": title, "body": "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"},
        )
    # troca a resposta do mock para o shape de review
    ai_client.app.state.ai_transport = _transport(
        json.dumps(review_payload, ensure_ascii=False)
    )
    resp = ai_client.post("/api/v1/ai/review/CT-0001", json={})
    assert resp.status_code == 200
    review = resp.json()
    assert review["preview"] is True
    assert {i["kind"] for i in review["issues"]} == {"duplicidade", "resultado_vago"}
    assert any(c["id"] == "CT-0002" for c in review["similar_considered"])


def test_negative_cases_returns_preview(ai_client):
    ai_client.post(
        "/api/v1/testcases",
        json={"title": "Login ok", "body": "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"},
    )
    resp = ai_client.post("/api/v1/ai/negative-cases/CT-0001", json={})
    assert resp.status_code == 200
    assert resp.json()["preview"] is True
    assert len(resp.json()["testcases"]) == 2
