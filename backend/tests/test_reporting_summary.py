"""Critério de aceite da spec reporting (0098) — resumo executivo narrado
pela IA, com os números reais injetados e incluído no export. MockTransport."""

import json

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

EXEC_SUMMARY = {
    "synthesis": "Qualidade estável, pass rate abaixo da meta.",
    "risks": ["Defeito crítico aberto", "Cobertura de execução parcial"],
    "recommendation": "Priorizar o smoke antes do full na próxima sprint.",
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


def _make_client(tmp_path, with_ai: bool):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    if with_ai:
        config["ai"] = {
            "default_provider": "local",
            "providers": [{"name": "local", "kind": "openai_compatible",
                           "base_url": "http://localhost:1234/v1", "model": "x"}],
        }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    app = create_app(
        ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
        ai_transport=_transport(json.dumps(EXEC_SUMMARY, ensure_ascii=False)),
        github_client=object(),
    )
    client = TestClient(app)
    client.ws = ws
    return client


@pytest.fixture()
def client(tmp_path):
    with _make_client(tmp_path, with_ai=True) as c:
        yield c


def _seed(client):
    """1 story, 2 CTs ready, 1 execution (1 passed, 1 failed), 1 defeito aberto."""
    st = client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Login"}
    ).json()
    ct1 = client.post(
        "/api/v1/testcases", json={"title": "ok", "status": "ready", "story": st["id"]}
    ).json()
    ct2 = client.post(
        "/api/v1/testcases", json={"title": "erro", "status": "ready", "story": st["id"]}
    ).json()
    ex = client.post(
        "/api/v1/executions",
        json={"name": "Regressão", "testcase_ids": [ct1["id"], ct2["id"]]},
    ).json()
    for ct_id, status in ((ct1["id"], "passed"), (ct2["id"], "failed")):
        client.post(
            f"/api/v1/executions/{ex['id']}/results/{ct_id}/status",
            json={"status": status},
        )
    client.post(
        "/api/v1/defects",
        json={"title": "quebra no login", "severity": "critical", "testcase": ct2["id"]},
    )


def test_executive_summary_injects_real_numbers_and_export_includes_it(client):
    _seed(client)
    resp = client.post("/api/v1/ai/executive-summary", json={}).json()
    assert resp["preview"] is True
    assert resp["synthesis"] == EXEC_SUMMARY["synthesis"]
    assert resp["risks"] == EXEC_SUMMARY["risks"]
    # os números REAIS foram injetados no contexto da IA (não inventados)
    ctx = resp["context_markdown"]
    assert "Pass rate: 50% (1/2)" in ctx
    assert "Total: 1" in ctx  # 1 defeito aberto
    assert "critical" in ctx

    # o resumo revisado entra no export como seção inicial
    edited = resp["synthesis"] + "\n\n" + resp["recommendation"]
    md = client.get(
        "/api/v1/metrics/traceability/export", params={"format": "md", "summary": edited}
    ).text
    assert "## Resumo executivo" in md
    assert resp["recommendation"] in md
    # a seção vem ANTES da tabela da matriz
    assert md.index("Resumo executivo") < md.index("Epic / Story")

    # export em PDF com resumo não quebra
    pdf = client.get(
        "/api/v1/metrics/traceability/export", params={"format": "pdf", "summary": edited}
    )
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"


def test_executive_summary_without_provider_is_409(tmp_path):
    """Sem provider, o endpoint recusa (409) e o dashboard segue funcional."""
    with _make_client(tmp_path, with_ai=False) as c:
        _seed(c)
        resp = c.post("/api/v1/ai/executive-summary", json={})
        assert resp.status_code == 409 and resp.json()["error"]["code"] == "ai_disabled"
        # export sem resumo continua funcionando
        md = c.get("/api/v1/metrics/traceability/export", params={"format": "md"}).text
        assert "## Resumo executivo" not in md
