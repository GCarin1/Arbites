"""Resumo de falha pós-run (0096) — POST /ai/analyze-run/{exec_id} devolve
resumo + causa provável + draft de defeito (preview); o aceite é o
POST /defects normal, já vinculado ao CT/execution. MockTransport httpx."""

import json

import httpx
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

ANALYSIS = {
    "summary": "O login falhou por timeout na chamada de autenticação.",
    "probable_cause": "Serviço de auth indisponível ou lento.",
    "defect": {
        "title": "Login falha por timeout na autenticação",
        "severity": "high",
        "description": "O CT de login falhou; a chamada de auth estourou o tempo.",
    },
}


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def get(self, provider):
        return self._keys.get(provider)


def _transport(content: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"choices": [{"message": {"content": content}}]}
        )

    return httpx.MockTransport(handler)


def _client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [{"name": "local", "kind": "openai_compatible",
                       "base_url": "http://localhost:1234/v1", "model": "qwen"}],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    app = create_app(
        ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
        ai_transport=_transport(json.dumps(ANALYSIS, ensure_ascii=False)),
        github_client=object(),
    )
    c = TestClient(app)
    c.ws = ws
    return c


def _failed_execution(c):
    ct = c.post("/api/v1/testcases", json={"title": "Login"}).json()
    ex = c.post(
        "/api/v1/executions", json={"name": "Reg", "testcase_ids": [ct["id"]]}
    ).json()
    c.post(
        f"/api/v1/executions/{ex['id']}/results/{ct['id']}/status",
        json={"status": "failed"},
    )
    return ct, ex


def test_analyze_run_returns_summary_and_defect_draft(tmp_path):
    with _client(tmp_path) as c:
        ct, ex = _failed_execution(c)
        r = c.post(f"/api/v1/ai/analyze-run/{ex['id']}", json={})
        assert r.status_code == 200, r.text
        out = r.json()
        assert out["preview"] is True
        assert "timeout" in out["summary"]
        assert out["defect"]["severity"] == "high"
        # o draft já vem vinculado ao CT e à execution
        assert out["defect"]["testcase"] == ct["id"]
        assert out["defect"]["execution"] == ex["id"]


def test_accept_draft_creates_linked_defect(tmp_path):
    with _client(tmp_path) as c:
        ct, ex = _failed_execution(c)
        draft = c.post(f"/api/v1/ai/analyze-run/{ex['id']}", json={}).json()["defect"]
        created = c.post("/api/v1/defects", json={
            "title": draft["title"], "severity": draft["severity"],
            "testcase": draft["testcase"], "execution": draft["execution"],
        }).json()
        assert created["testcase_id"] == ct["id"]
        assert created["execution_id"] == ex["id"]


def test_analyze_run_without_failures_is_422(tmp_path):
    with _client(tmp_path) as c:
        ct = c.post("/api/v1/testcases", json={"title": "Passa"}).json()
        ex = c.post(
            "/api/v1/executions", json={"name": "R", "testcase_ids": [ct["id"]]}
        ).json()
        c.post(f"/api/v1/executions/{ex['id']}/results/{ct['id']}/status",
               json={"status": "passed"})
        r = c.post(f"/api/v1/ai/analyze-run/{ex['id']}", json={})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "no_failures"


def test_analyze_run_unknown_execution_is_404(tmp_path):
    with _client(tmp_path) as c:
        assert c.post("/api/v1/ai/analyze-run/EXEC-9999", json={}).status_code == 404
