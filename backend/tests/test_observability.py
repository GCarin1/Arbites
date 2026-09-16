"""A aba de Observabilidade (change 0155, ADR 0016) — o lado do servidor.

O que separa esta tela do Dashboard não é o nome, é o EIXO: o Dashboard
responde "como está agora", aqui a pergunta é "o que mudou, quando e por
quê". Por isso todo teste abaixo olha para a COMPARAÇÃO e para a DESCIDA —
número sozinho e gráfico sem caminho para o print seriam mural, não
observabilidade.
"""

import json

import pytest
import yaml
from conftest import login_admin
from fastapi.testclient import TestClient
from test_ci_ingest import FakeGitHub, FakeTokenStore, _zip, manifesto

from arbites.api import create_app
from arbites.ci_ingest import MANIFESTO


def _monta(ws, goals=None):
    config = ws.config()
    config["observability"] = {
        "sources": [{"provider": "github", "repo": "org/app"}],
        "max_runs_per_poll": 50,
    }
    if goals:
        config["observability"]["goals"] = goals
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    fake = FakeGitHub()
    app = create_app(ws.root, watch=False,
                     github_client=fake, token_store=FakeTokenStore())
    client = TestClient(app)
    client.__enter__()
    login_admin(client)
    client.fake = fake
    client.ws = ws
    return client


@pytest.fixture()
def rig(ws):
    client = _monta(ws)
    yield client
    client.__exit__(None, None, None)


def _hoje(dia: int) -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(days=dia)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def test_periodo_vazio_responde_sem_quebrar(rig):
    """Estado vazio é resposta, não erro: a instância recém-instalada abre a
    aba antes de existir um único run."""
    painel = rig.get("/api/v1/ci/observability?days=30").json()
    assert painel["health"]["runs"] == 0
    assert painel["health"]["success_rate"] is None
    assert painel["signals"] == []
    assert painel["changes"] == []


def test_saude_traz_o_periodo_anterior_ao_lado(rig):
    """Um número sozinho não diz se está melhorando. 75% só significa alguma
    coisa ao lado dos 100% da semana passada."""
    for dia in (40, 38):  # período anterior: dois verdes
        rig.fake.adicionar(1000 + dia, started=_hoje(dia),
                           artifact=_zip({MANIFESTO: manifesto([])}))
    rig.fake.adicionar(2001, started=_hoje(5), conclusion="failure",
                       artifact=_zip({MANIFESTO: manifesto([])}))
    rig.fake.adicionar(2002, started=_hoje(3),
                       artifact=_zip({MANIFESTO: manifesto([])}))
    rig.post("/api/v1/ci/ingest")

    saude = rig.get("/api/v1/ci/observability?days=30").json()["health"]
    assert saude["runs"] == 2
    assert saude["runs_previous"] == 2
    assert saude["success_rate"] == 50.0
    assert saude["success_rate_previous"] == 100.0


def test_do_ponto_da_serie_chega_ao_run_ao_job_e_ao_anexo(rig):
    """A descida obrigatória. Sem ela o gráfico é decoração: o pico aparece e
    não há caminho até o print que mostra o que aconteceu."""
    rig.fake.jobs_de = {}
    rig.fake.adicionar(101, started=_hoje(2), artifact=_zip({
        MANIFESTO: manifesto(
            [{"kind": "perf", "name": "lcp_ms", "value": 3100, "unit": "ms"}],
            [{"kind": "screenshot", "path": "home.png"}],
        ),
        "home.png": b"\x89PNG\r\n\x1a\nfake",
    }))
    rig.post("/api/v1/ci/ingest")

    # 1. o ponto do gráfico carrega o run
    sinal = rig.get("/api/v1/ci/observability?days=30").json()["signals"][0]
    ponto = sinal["points"][-1]
    assert ponto["run_id"] == "github-101"

    # 2. o run carrega job e anexo
    run = rig.get(f"/api/v1/ci/runs/{ponto['run_id']}").json()
    assert [j["name"] for j in run["jobs"]] == ["testes-e2e"]
    anexo = run["attachments"][0]

    # 3. e o anexo abre
    arquivo = rig.get("/api/v1/ci/attachment", params={"path": anexo["path"]})
    assert arquivo.status_code == 200
    assert arquivo.content.startswith(b"\x89PNG")


def test_analise_da_ia_volta_como_corpo_do_run(rig):
    corpo = "# Análise\n\nO tempo de carga subiu 30% nesta semana.\n"
    rig.fake.adicionar(101, started=_hoje(1), artifact=_zip({
        MANIFESTO: manifesto([], [{"kind": "analysis", "path": "analysis.md"}]),
        "analysis.md": corpo.encode("utf-8"),
    }))
    rig.post("/api/v1/ci/ingest")

    run = rig.get("/api/v1/ci/runs/github-101").json()
    assert "subiu 30%" in run["analysis"]


def test_anexo_fora_da_pasta_de_ci_e_recusado(rig):
    """O caminho vem do índice, mas a contenção é verificada no disco: índice
    adulterado não pode virar leitura de arquivo arbitrário."""
    for caminho in ("../arbites.yaml", "ci/../arbites.yaml",
                    "/etc/passwd", "requirements/qualquer.md"):
        resposta = rig.get("/api/v1/ci/attachment", params={"path": caminho})
        assert resposta.status_code == 404, caminho


def test_sem_direcao_declarada_o_arbites_nao_julga(rig):
    """Ele não sabe que `lcp_ms` maior é pior. Sem `direction` no arbites.yaml
    a frase diz que SUBIU, não que piorou — inventar a direção seria opinião
    disfarçada de medição."""
    rig.fake.adicionar(101, started=_hoje(40), artifact=_zip({
        MANIFESTO: manifesto([{"name": "lcp_ms", "value": 2000, "unit": "ms"}])}))
    rig.fake.adicionar(102, started=_hoje(2), artifact=_zip({
        MANIFESTO: manifesto([{"name": "lcp_ms", "value": 3000, "unit": "ms"}])}))
    rig.post("/api/v1/ci/ingest")

    mudancas = rig.get("/api/v1/ci/observability?days=30").json()["changes"]
    frase = next(m["text"] for m in mudancas if m.get("signal") == "lcp_ms")
    assert "subiu 50.0%" in frase
    assert "piorou" not in frase


def test_com_direcao_e_meta_declaradas_a_saude_e_dita_nao_inferida(ws):
    """"87% contra a meta de 95%, caindo" — a meta vem de quem instala."""
    rig = _monta(ws, goals={"lcp_ms": {"direction": "lower", "goal": 2500}})
    try:
        rig.fake.adicionar(101, started=_hoje(40), artifact=_zip({
            MANIFESTO: manifesto([{"name": "lcp_ms", "value": 2000, "unit": "ms"}])}))
        rig.fake.adicionar(102, started=_hoje(2), artifact=_zip({
            MANIFESTO: manifesto([{"name": "lcp_ms", "value": 3000, "unit": "ms"}])}))
        rig.post("/api/v1/ci/ingest")

        painel = rig.get("/api/v1/ci/observability?days=30").json()
        sinal = next(s for s in painel["signals"] if s["name"] == "lcp_ms")
        assert sinal["goal"] == 2500 and sinal["direction"] == "lower"

        mudanca = next(m for m in painel["changes"] if m.get("signal") == "lcp_ms")
        assert "piorou 50.0%" in mudanca["text"]
        assert mudanca["goal_miss"] is True
    finally:
        rig.__exit__(None, None, None)


def test_silencio_da_ingestao_e_dito_em_vez_de_parecer_semana_tranquila(rig):
    """Ausência de dado se parece com boa notícia num gráfico. É a pior
    armadilha de um painel — então ela é nomeada."""
    rig.fake.adicionar(101, started=_hoje(9),
                       artifact=_zip({MANIFESTO: manifesto([])}))
    rig.post("/api/v1/ci/ingest")

    painel = rig.get("/api/v1/ci/observability?days=30").json()
    silencio = next(m for m in painel["changes"] if m["kind"] == "silence")
    assert "há 9 dias" in silencio["text"]
    assert painel["health"]["days_since_last_run"] == 9


def test_quebra_depois_de_sequencia_verde_aponta_o_run(rig):
    for dia in (8, 6, 4):
        rig.fake.adicionar(100 + dia, started=_hoje(dia),
                           artifact=_zip({MANIFESTO: manifesto([])}))
    rig.fake.adicionar(200, started=_hoje(1), conclusion="failure",
                       artifact=_zip({MANIFESTO: manifesto([])}))
    rig.post("/api/v1/ci/ingest")

    mudanca = next(m for m in rig.get("/api/v1/ci/observability?days=30")
                   .json()["changes"] if m["kind"] == "broke")
    assert mudanca["run_id"] == "github-200"
    # o adjetivo concorda junto com o substantivo (change 0177)
    assert "3 execuções verdes seguidas" in mudanca["text"]


def test_run_sem_manifesto_aparece_no_que_mudou(rig):
    rig.fake.adicionar(101, started=_hoje(1),
                       artifact=_zip({"erro.log": b"stacktrace\n"}))
    rig.post("/api/v1/ci/ingest")

    aviso = next(m for m in rig.get("/api/v1/ci/observability?days=30")
                 .json()["changes"] if m["kind"] == "convention")
    assert MANIFESTO in aviso["text"]


def test_periodo_invalido_e_recusado(rig):
    assert rig.get("/api/v1/ci/observability?days=0").status_code == 422
    assert rig.get("/api/v1/ci/observability?days=900").status_code == 422
