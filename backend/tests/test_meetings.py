"""Critérios de aceite da spec meetings (SC13)."""

import json
from datetime import date

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

TODAY = date.today().isoformat()

SUMMARY = {
    "summary": "Alinhamento da regressão da sprint; ambiente instável.",
    "decisions": ["Priorizar smoke antes do full"],
    "action_items": ["Abrir defeito do ambiente"],
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
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

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
                     ai_transport=_transport(json.dumps(SUMMARY, ensure_ascii=False)),
                     github_client=object())
    with TestClient(app) as c:
        c.ws = ws
        yield c


def test_meeting_crud_and_filter_by_date(client):
    """SC13.1: CRUD persistido em meetings/*.md, listagem por data."""
    m = client.post(
        "/api/v1/meetings",
        json={"title": "Daily sync", "date": TODAY, "body": "Falamos da regressão."},
    ).json()
    assert m["id"].startswith("MTG-") and m["date"] == TODAY
    files = list((client.ws.root / "meetings").glob("*.md"))
    assert len(files) == 1 and "Falamos da regressão." in files[0].read_text(encoding="utf-8")

    client.post("/api/v1/meetings", json={"title": "Outra", "date": "2026-01-01"})
    today_only = client.get("/api/v1/meetings", params={"date": TODAY}).json()
    assert [x["title"] for x in today_only] == ["Daily sync"]

    assert client.delete(f"/api/v1/meetings/{m['id']}").status_code == 204


def test_summarize_is_preview_then_save(client):
    """SC13.2: resumo em preview, sem gravar; salvar persiste `summary`."""
    m = client.post(
        "/api/v1/meetings",
        json={"title": "Planning", "body": "Discussão longa sobre a sprint."},
    ).json()
    resp = client.post(f"/api/v1/meetings/{m['id']}/summarize", json={}).json()
    assert resp["preview"] is True and resp["summary"]
    assert resp["decisions"] and resp["action_items"]
    # ainda não gravou o summary
    assert client.get(f"/api/v1/meetings/{m['id']}").json()["summary"] is None
    # aceitar = salvar
    saved = client.put(
        f"/api/v1/meetings/{m['id']}", json={"summary": resp["summary"]}
    ).json()
    assert saved["summary"] == resp["summary"]


def test_summarize_empty_body_rejected(client):
    m = client.post("/api/v1/meetings", json={"title": "Vazia", "body": ""}).json()
    resp = client.post(f"/api/v1/meetings/{m['id']}/summarize", json={})
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "empty_meeting"


def test_meetings_appear_in_daily_context(client):
    """SC13.3: reuniões do dia entram no contexto da daily."""
    m = client.post(
        "/api/v1/meetings", json={"title": "Retro", "date": TODAY, "body": "Retro da sprint."}
    ).json()
    client.put(f"/api/v1/meetings/{m['id']}", json={"summary": "Melhorar a automação."})
    ctx = client.get(f"/api/v1/daily/{TODAY}/context").json()
    assert any(x["id"] == m["id"] for x in ctx["meetings"])
    assert "Reuniões do dia" in ctx["markdown"] and "Melhorar a automação." in ctx["markdown"]


MEETING_BODY = (
    "# Retro da sprint\n\n"
    "Discutimos a regressão.\n\n"
    "## Action items\n"
    "- [ ] Abrir defeito do ambiente instável\n"
    "- [ ] Revisar o smoke antes do full\n"
    "- [x] Item já feito não conta\n"
    "- linha comum não é action item\n"
)


def test_action_items_deterministic_extraction_and_accept(client):
    """0097: linhas `- [ ]` viram preview; aceite cria afazeres vinculados à
    reunião. O caminho determinístico não usa IA."""
    m = client.post(
        "/api/v1/meetings", json={"title": "Retro", "body": MEETING_BODY}
    ).json()

    preview = client.get(f"/api/v1/meetings/{m['id']}/action-items").json()
    assert preview["deterministic"] == [
        "Abrir defeito do ambiente instável",
        "Revisar o smoke antes do full",
    ]
    assert preview["converted"] == []

    accept = client.post(
        f"/api/v1/meetings/{m['id']}/action-items/accept",
        json={"items": preview["deterministic"]},
    )
    assert accept.status_code == 201
    created = accept.json()["created"]
    assert len(created) == 2

    # cada afazer aponta de volta para a reunião (link no todo)
    todo = client.get(f"/api/v1/todos/{created[0]}").json()
    assert any(link["id"] == m["id"] for link in todo["links"])

    # histórico dos já convertidos aparece no preview seguinte
    after = client.get(f"/api/v1/meetings/{m['id']}/action-items").json()
    assert sorted(t["id"] for t in after["converted"]) == sorted(created)


def test_action_items_ai_generate_preview(client):
    """0097: extração assistida por IA devolve preview (mesmo mock da daily)."""
    m = client.post(
        "/api/v1/meetings", json={"title": "Planning", "body": "Discussão longa."}
    ).json()
    resp = client.post(
        f"/api/v1/meetings/{m['id']}/action-items/generate", json={}
    ).json()
    assert resp["preview"] is True
    assert resp["action_items"] == SUMMARY["action_items"]
    # aceite dos itens da IA também cria afazeres vinculados
    accept = client.post(
        f"/api/v1/meetings/{m['id']}/action-items/accept",
        json={"items": resp["action_items"]},
    ).json()
    assert len(accept["created"]) == len(SUMMARY["action_items"])
