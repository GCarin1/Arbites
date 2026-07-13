"""Memória Histórica do Projeto — linha do tempo cronológica (estilo git
log) cruzando requisitos, defeitos, lições aprendidas, decisões
arquiteturais e interações de agentes de IA; e o recap dessas decisões e
lições injetado nas chamadas de IA que geram conteúdo (generate-testcases,
review), para que a IA "fique mais inteligente conforme o projeto cresce".
"""

import json

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"

GENERATED = {
    "testcases": [
        {
            "title": "Caso gerado", "type": "manual", "priority": "medium", "tags": [],
            "objetivo": "o", "pre_condicoes": [], "passos": ["p1"],
            "resultado_esperado": "ok",
        }
    ]
}
REVIEWED = {"issues": [], "summary": "ok"}


def test_timeline_aggregates_requirement_defect_and_decision(client):
    epic = client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"}).json()
    d = client.post("/api/v1/defects", json={"title": "Bug", "severity": "high"}).json()
    dec = client.post("/api/v1/decisions", json={"title": "Dec", "status": "accepted"}).json()

    events = client.get("/api/v1/memory/timeline").json()
    by_id = {e["id"]: e for e in events}
    assert by_id[epic["id"]]["kind"] == "requirement"
    assert by_id[d["id"]]["kind"] == "defect"
    assert by_id[dec["id"]]["kind"] == "decision"


def test_timeline_derives_lesson_event_only_when_root_cause_present(client):
    with_lesson = client.post(
        "/api/v1/defects",
        json={"title": "Com lição", "root_cause": "causa X", "fix": "correção Y"},
    ).json()
    without_lesson = client.post("/api/v1/defects", json={"title": "Sem lição"}).json()

    events = client.get("/api/v1/memory/timeline").json()
    lesson_ids = [e["id"] for e in events if e["kind"] == "lesson"]
    assert with_lesson["id"] in lesson_ids
    assert without_lesson["id"] not in lesson_ids
    # o defeito COM lição também aparece como evento "defect" separado
    defect_ids = [e["id"] for e in events if e["kind"] == "defect"]
    assert with_lesson["id"] in defect_ids


def test_timeline_kinds_filter(client):
    client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"})
    client.post("/api/v1/decisions", json={"title": "Dec"})

    only_decisions = client.get(
        "/api/v1/memory/timeline", params={"kinds": "decision"}
    ).json()
    assert all(e["kind"] == "decision" for e in only_decisions)
    assert len(only_decisions) == 1


def test_timeline_limit(client):
    for i in range(5):
        client.post("/api/v1/decisions", json={"title": f"Dec {i}"})
    events = client.get("/api/v1/memory/timeline", params={"limit": 2}).json()
    assert len(events) == 2


def test_timeline_empty_workspace_returns_no_events(client):
    assert client.get("/api/v1/memory/timeline").json() == []


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


def _recording_transport(content: str, sink: list):
    def handler(request: httpx.Request) -> httpx.Response:
        sink.append(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": content}}]},
        )

    return httpx.MockTransport(handler)


@pytest.fixture()
def memory_client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [
            {"name": "local", "kind": "openai_compatible",
             "base_url": "http://localhost:1234/v1", "model": "qwen"},
        ],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    requests: list = []
    app = create_app(
        ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
        ai_transport=_recording_transport(json.dumps(GENERATED, ensure_ascii=False), requests),
        github_client=object(),
    )
    with TestClient(app) as c:
        c.ws = ws
        c.requests = requests
        yield c


def test_generate_testcases_logs_agent_event(memory_client):
    story = memory_client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Checkout"}
    ).json()
    memory_client.post("/api/v1/ai/generate-testcases", json={"source": story["id"]})

    events = memory_client.get("/api/v1/memory/timeline").json()
    agent_events = [e for e in events if e["kind"] == "agent"]
    assert len(agent_events) == 1
    assert agent_events[0]["title"] == "Checkout"
    assert "1 caso" in agent_events[0]["summary"]


@pytest.fixture()
def review_client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [
            {"name": "local", "kind": "openai_compatible",
             "base_url": "http://localhost:1234/v1", "model": "qwen"},
        ],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    requests: list = []
    app = create_app(
        ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
        ai_transport=_recording_transport(json.dumps(REVIEWED, ensure_ascii=False), requests),
        github_client=object(),
    )
    with TestClient(app) as c:
        c.ws = ws
        c.requests = requests
        yield c


def test_generate_testcases_injects_recent_recap_into_prompt(memory_client):
    memory_client.post(
        "/api/v1/decisions", json={"title": "Usar Decimal para dinheiro", "status": "accepted"}
    )
    memory_client.post(
        "/api/v1/defects",
        json={"title": "Bug antigo", "root_cause": "arredondamento com float", "fix": "usar Decimal"},
    )
    story = memory_client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Checkout"}
    ).json()

    memory_client.post("/api/v1/ai/generate-testcases", json={"source": story["id"]})

    sent = memory_client.requests[0]
    user_msg = next(m["content"] for m in sent["messages"] if m["role"] == "user")
    assert "Usar Decimal para dinheiro" in user_msg
    assert "arredondamento com float" in user_msg


def test_review_logs_agent_event_and_gets_recap(review_client):
    review_client.post(
        "/api/v1/decisions", json={"title": "Padrão de nomenclatura de CT", "status": "accepted"}
    )
    ct = review_client.post(
        "/api/v1/testcases", json={"title": "CT 1", "body": TC_BODY}
    ).json()

    resp = review_client.post(f"/api/v1/ai/review/{ct['id']}", json={})
    assert resp.status_code == 200

    sent = review_client.requests[0]
    user_msg = next(m["content"] for m in sent["messages"] if m["role"] == "user")
    assert "Padrão de nomenclatura de CT" in user_msg

    events = review_client.get("/api/v1/memory/timeline").json()
    agent_events = [e for e in events if e["kind"] == "agent"]
    assert len(agent_events) == 1
    assert agent_events[0]["id"] == ct["id"] or agent_events[0]["title"] == "CT 1"


def test_negative_cases_logs_agent_event(memory_client):
    ct = memory_client.post(
        "/api/v1/testcases", json={"title": "CT 1", "body": TC_BODY}
    ).json()
    memory_client.post(f"/api/v1/ai/negative-cases/{ct['id']}", json={})

    events = memory_client.get("/api/v1/memory/timeline").json()
    agent_events = [e for e in events if e["kind"] == "agent"]
    assert len(agent_events) == 1
    assert "negativo" in agent_events[0]["summary"]


def test_recap_empty_string_when_no_decisions_or_lessons(memory_client):
    story = memory_client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Checkout"}
    ).json()
    memory_client.post("/api/v1/ai/generate-testcases", json={"source": story["id"]})

    sent = memory_client.requests[0]
    user_msg = next(m["content"] for m in sent["messages"] if m["role"] == "user")
    assert "Histórico recente do projeto" not in user_msg


def test_agent_log_failure_does_not_lose_ai_response(memory_client):
    """Bug real: se gravar o log de agente falhasse (disco/lock), a exceção
    subia e o usuário perdia o conteúdo que o LLM JÁ tinha gerado — o log é
    acessório, a resposta é o produto."""
    import shutil

    story = memory_client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Checkout"}
    ).json()
    # sabota o diretório: agent_log vira um ARQUIVO, mkdir/write vai falhar
    agent_dir = memory_client.ws.root / "agent_log"
    shutil.rmtree(agent_dir)
    agent_dir.write_text("não sou um diretório", encoding="utf-8")

    resp = memory_client.post(
        "/api/v1/ai/generate-testcases", json={"source": story["id"]}
    )
    assert resp.status_code == 200  # resposta preservada
    assert resp.json()["testcases"]  # conteúdo gerado chegou inteiro


def test_agent_event_survives_reindex(memory_client):
    story = memory_client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Checkout"}
    ).json()
    memory_client.post("/api/v1/ai/generate-testcases", json={"source": story["id"]})
    memory_client.post("/api/v1/workspace/reindex")

    events = memory_client.get("/api/v1/memory/timeline").json()
    assert len([e for e in events if e["kind"] == "agent"]) == 1
