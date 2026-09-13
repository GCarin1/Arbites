"""Critérios de aceite do dashboard reorganizado (change 0114).

Duas afirmações, e a segunda é a que importa: o bloco "O que precisa de
atenção" sai dos números que o produto JÁ apura, e o dashboard inteiro
continua correto com a IA desligada — o indicador vem do índice, a IA é só
a melhor redação da leitura dele.
"""

import httpx
import json as jsonlib
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites import metrics as metrics_ops
from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

from conftest import login_admin

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir\n2. Agir\n\n"
    "## Resultado esperado\n\nOk.\n"
)

KPIS = ("requirement_coverage", "execution_coverage", "pass_rate",
        "blocked_rate", "rework_rate")


def cenario(client):
    """Um ciclo com um caso passado e um falhado — números de verdade para
    os indicadores do topo lerem."""
    cts = [
        client.post("/api/v1/testcases",
                    json={"title": f"Caso {i}", "body": TC_BODY}).json()
        for i in range(2)
    ]
    execution = client.post(
        "/api/v1/executions",
        json={"name": "Regressão", "sprint": "Sprint 42",
              "environment": "homolog",
              "testcase_ids": [c["id"] for c in cts]},
    ).json()
    for ct, status in zip(cts, ["passed", "failed"]):
        client.post(
            f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
            json={"status": status, "column": status, "who": "carini"},
        )
    return execution, cts


# -- AC1: a linha de indicadores e o contexto do bloco ---------------------


def test_linha_de_indicadores_vem_dos_numeros_ja_apurados(client):
    cenario(client)
    summary = client.get("/api/v1/metrics/summary?sprint=Sprint 42").json()
    for kpi in KPIS:
        assert kpi in summary, kpi
    # pass rate real do cenário: 1 de 2
    assert summary["pass_rate"]["value"] == pytest.approx(0.5)
    # e o health score, que fecha a linha, é apurado do mesmo índice
    health = client.get("/api/v1/metrics/health").json()
    assert "score" in health


def test_contexto_do_bloco_de_atencao_traz_os_mesmos_indicadores(client):
    """O texto narrado é escrito a partir DESTE contexto — se um indicador
    não estiver aqui, a IA não tem como falar dele sem inventar."""
    cenario(client)
    contexto = metrics_ops.executive_context_markdown(
        client.app.state.conn, "Sprint 42", None
    )
    assert "Métricas" in contexto
    for rotulo in ("Pass rate", "Cobertura", "sprint=Sprint 42"):
        assert rotulo in contexto, rotulo


def test_bloco_de_atencao_tem_alertas_e_acoes_do_periodo(client):
    """A fonte determinística do bloco: alertas e ações que o dashboard já
    devolve, com ou sem IA."""
    cenario(client)
    overview = client.get("/api/v1/metrics/dashboard?sprint=Sprint 42").json()
    assert isinstance(overview["alerts"], list)
    assert isinstance(overview["recommended_actions"], list)
    for action in overview["recommended_actions"]:
        assert action["message"]


# -- AC2: o dashboard inteiro funciona com a IA desligada -----------------


def test_dashboard_inteiro_responde_sem_provider_de_ia(client):
    """Nenhum número depende da IA. Sem provider, tudo continua de pé."""
    cenario(client)
    assert client.get("/api/v1/ai/providers").json()["default_provider"] in (None, "")
    for rota in (
        "/api/v1/metrics/summary",
        "/api/v1/metrics/health",
        "/api/v1/metrics/dashboard",
        "/api/v1/metrics/trend?days=7",
        "/api/v1/metrics/defects",
    ):
        assert client.get(rota).status_code == 200, rota


def test_resumo_narrado_sem_provider_recusa_sem_derrubar_o_dashboard(client):
    cenario(client)
    recusado = client.post("/api/v1/ai/executive-summary", json={})
    assert recusado.status_code == 409
    # e o dashboard segue respondendo logo depois da recusa
    assert client.get("/api/v1/metrics/dashboard").status_code == 200


NARRADO = {
    "synthesis": "Pass rate em 50% no período, puxado por uma falha.",
    "risks": ["Um caso falhando na Sprint 42"],
    "recommendation": "Investigar a falha antes de fechar o ciclo.",
}


@pytest.fixture()
def com_ia(tmp_path):
    """Instância com provider de IA configurado e transporte falso."""
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

    enviados: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        enviados.append(jsonlib.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {
                "content": jsonlib.dumps(NARRADO, ensure_ascii=False)}}]},
        )

    class FakeKeyStore(AIKeyStore):
        def __init__(self):
            self._keys = {}

        def set(self, provider, key):
            self._keys[provider] = key

        def get(self, provider):
            return self._keys.get(provider)

    app = create_app(ws.root, watch=False, ai_key_store=FakeKeyStore(),
                     ai_transport=httpx.MockTransport(handler))
    with TestClient(app) as client:
        login_admin(client)
        client.ws = ws
        yield client, enviados


def test_com_provider_o_resumo_e_narrado_a_partir_dos_mesmos_numeros(com_ia):
    client, enviados = com_ia
    cenario(client)

    resumo = client.post(
        "/api/v1/ai/executive-summary", json={"sprint": "Sprint 42"}
    ).json()
    assert resumo["synthesis"] == NARRADO["synthesis"]
    assert resumo["risks"] == NARRADO["risks"]
    # o contexto factual vai junto na resposta e no prompt: a IA narra os
    # números apurados, não os inventa
    assert "Pass rate" in resumo["context_markdown"]
    assert "Pass rate" in enviados[-1]["messages"][-1]["content"]


def test_com_provider_os_indicadores_continuam_vindo_do_indice(com_ia):
    """A IA entrou, e o número não mudou de fonte."""
    client, _ = com_ia
    cenario(client)
    summary = client.get("/api/v1/metrics/summary?sprint=Sprint 42").json()
    assert summary["pass_rate"]["value"] == pytest.approx(0.5)
