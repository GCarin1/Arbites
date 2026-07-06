"""Critérios de aceite da spec daily (SC12) — contexto do dia + digest IA."""

import json
from datetime import date, timedelta

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"
TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()

DIGEST = {
    "summary": "Rodei a regressão de login; 1 falha virou defeito.",
    "impediments": ["Ambiente de homolog instável"],
    "progress": "Cobertura estável; 1 defeito aberto.",
    "action_items": ["Reabrir CT-0001 após correção", "Cobrar fix do ambiente"],
}


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


def _transport(content: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"choices": [{"message": {"content": content}}]}
        )

    return httpx.MockTransport(handler)


@pytest.fixture()
def client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [{"name": "local", "kind": "openai_compatible",
                       "base_url": "http://localhost:1234/v1", "model": "x"}],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    app = create_app(ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
                     ai_transport=_transport(json.dumps(DIGEST, ensure_ascii=False)),
                     github_client=object())
    with TestClient(app) as c:
        c.ws = ws
        yield c


def _seed(client):
    client.post("/api/v1/todos", json={"title": "Ambiente caiu", "status": "blocked"})
    ct = client.post("/api/v1/testcases", json={"title": "Login", "body": TC_BODY}).json()
    execution = client.post(
        "/api/v1/executions", json={"name": "Reg", "testcase_ids": [ct["id"]]}
    ).json()
    client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
        json={"status": "failed"},
    )
    client.post("/api/v1/defects", json={"title": "Falha login", "severity": "high",
                                         "testcase": ct["id"], "execution": execution["id"]})
    return ct, execution


def test_snapshot_and_metrics_diff(client):
    """SC12.1: snapshot por dia e diff do dia vs. anterior."""
    _seed(client)
    snap = client.post("/api/v1/metrics/snapshot").json()
    assert snap["date"] == TODAY and "pass_rate" in snap["metrics"]
    # snapshot de ontem, à mão, para o diff
    (client.ws.root / "metrics" / f"{YESTERDAY}.json").write_text(
        json.dumps({"date": YESTERDAY, "metrics": {"pass_rate": 1.0}}), encoding="utf-8"
    )
    ctx = client.get(f"/api/v1/daily/{TODAY}/context").json()
    diff = ctx["metrics_diff"]
    assert diff["has_today"] and diff["has_previous"]
    pass_rate = next(m for m in diff["metrics"] if m["metric"] == "pass_rate")
    assert pass_rate["previous"] == 1.0 and pass_rate["delta"] is not None


def test_context_aggregates_todos_activity_defects(client):
    """SC12.2: contexto junta todos (bloqueados), atividade e defeitos."""
    _seed(client)
    ctx = client.get(f"/api/v1/daily/{TODAY}/context").json()
    assert len(ctx["todos"]["blocked"]) == 1
    assert len(ctx["activity"]["defects_opened"]) == 1
    assert ctx["defects_open"]["open_count"] == 1
    assert "Impedimentos" in ctx["markdown"] and "Defeitos abertos" in ctx["markdown"]


def test_generate_daily_is_preview_and_writes_nothing(client):
    """SC12.3: gerar devolve resumo/impedimentos/andamento/action items em preview."""
    _seed(client)
    resp = client.post(f"/api/v1/daily/{TODAY}/generate", json={}).json()
    assert resp["preview"] is True
    assert resp["summary"] and resp["progress"]
    assert resp["impediments"] and resp["action_items"]
    # nada gravado
    assert client.get("/api/v1/dailies").json()["dailies"] == []
    assert client.get(f"/api/v1/daily/{TODAY}").status_code == 404


def test_save_daily_and_action_item_becomes_todo(client):
    """SC12.4: salvar persiste e lista; action item vira todo."""
    saved = client.put(
        f"/api/v1/daily/{TODAY}",
        json={"body": "Texto da daily.", "action_items": DIGEST["action_items"]},
    ).json()
    assert saved["date"] == TODAY
    assert client.get("/api/v1/dailies").json()["dailies"] == [TODAY]
    fetched = client.get(f"/api/v1/daily/{TODAY}").json()
    assert fetched["body"].strip() == "Texto da daily." and len(fetched["action_items"]) == 2

    # aceitar um action item → cria todo
    todo = client.post(
        "/api/v1/todos", json={"title": DIGEST["action_items"][0]}
    ).json()
    assert todo["title"] == DIGEST["action_items"][0]
    assert any(t["id"] == todo["id"] for t in client.get("/api/v1/todos").json())


def test_daily_context_without_ai_still_works(client):
    """State-driven: contexto disponível para escrita manual (sem chamar IA)."""
    ctx = client.get(f"/api/v1/daily/{TODAY}/context").json()
    assert ctx["date"] == TODAY and "markdown" in ctx
