"""O repositório que DISPAROU a suíte (change 0178).

Três repositórios diferentes no mesmo evento: onde o teste mora, onde a
aplicação mora e quem mandou rodar. "Qual produto está quebrando" é sobre o
segundo — e até aqui só o primeiro existia, então um repositório de teste que
serve trader, ordens e app reunia os três numa taxa só.
"""

from datetime import datetime, timedelta, timezone

import pytest
from conftest import logged_in_client

from arbites.ci_ingest import (
    erros_por_origem, escrever_run, normalizar_gatilho, por_origem,
)
from arbites.indexer import connect, reindex_file

AGORA = datetime.now(timezone.utc)


# -- leitura do manifesto ----------------------------------------------------

def test_o_bloco_trigger_e_a_fonte_principal():
    gatilho = normalizar_gatilho(
        {"trigger": {"repo": "b3/app-trader-web", "environment": "prd",
                     "ref": "v1.4.0"}}, {})
    assert gatilho == {"repo": "b3/app-trader-web", "environment": "prd",
                       "ref": "v1.4.0"}


@pytest.mark.parametrize("chave", ["repository", "source_repo"])
def test_nomes_alternativos_do_repositorio(chave):
    """Um workflow corporativo nomeia o campo do jeito dele."""
    assert normalizar_gatilho({"trigger": {chave: "org/app"}}, {})["repo"] == "org/app"


def test_rotulo_serve_de_origem_quando_nao_ha_bloco():
    """Quem já usa `labels` não precisa migrar nada."""
    gatilho = normalizar_gatilho({}, {"repo_origem": "b3/app-ordens-web",
                                      "ambiente": "hml"})
    assert gatilho["repo"] == "b3/app-ordens-web"
    assert gatilho["environment"] == "hml"


def test_o_bloco_ganha_do_rotulo():
    gatilho = normalizar_gatilho({"trigger": {"repo": "do-bloco"}},
                                 {"repo_origem": "do-rotulo"})
    assert gatilho["repo"] == "do-bloco"


def test_sem_nada_declarado_nao_inventa_origem():
    assert normalizar_gatilho({}, {}) == {}
    assert normalizar_gatilho({"trigger": "nao e dict"}, {}) == {}


# -- recorte -----------------------------------------------------------------

def _grava(ws, conn, chave, repo_teste, origem, conclusao, dias_atras):
    quando = (AGORA - timedelta(days=dias_atras)).isoformat()
    run = {"key": chave, "provider": "github", "repo": repo_teste,
           "workflow": "deploy-e2e.yml", "run_id": chave.split("-")[-1],
           "conclusion": conclusao, "started_at": quando, "ingested_at": quando}
    manifesto = {"version": 2, "trigger": {"repo": origem} if origem else {}}
    gravado = escrever_run(ws.root, run, manifesto, {}, None)
    reindex_file(ws, conn, ws.root / gravado["path"])


@pytest.fixture()
def suite_compartilhada(ws):
    """UM repositório de teste servindo DOIS produtos — o caso que a taxa
    global do repositório de teste esconde."""
    conn = connect(ws)
    for i in range(1, 5):   # trader: metade falha
        _grava(ws, conn, f"github-1{i}", "b3/e2e-web", "b3/app-trader-web",
               "success" if i > 2 else "failure", i)
    for i in range(1, 5):   # ordens: tudo verde
        _grava(ws, conn, f"github-2{i}", "b3/e2e-web", "b3/app-ordens-web",
               "success", i)
    return ws, conn


def _janela():
    return ((AGORA - timedelta(days=60)).isoformat(),
            (AGORA - timedelta(days=30)).isoformat(),
            (AGORA + timedelta(days=1)).isoformat())


def test_cada_produto_tem_a_propria_taxa(suite_compartilhada):
    _, conn = suite_compartilhada
    linhas = {r["name"]: r for r in por_origem(conn, *_janela())}
    assert linhas["b3/app-trader-web"]["success_rate"] == 50.0
    assert linhas["b3/app-ordens-web"]["success_rate"] == 100.0


def test_o_grafico_de_erros_conta_volume_nao_taxa(suite_compartilhada):
    """90% em mil execuções são cem falhas; 50% em duas são uma. Quem vai
    atrás do problema precisa do segundo número."""
    _, conn = suite_compartilhada
    _, inicio, fim = _janela()
    fatias = erros_por_origem(conn, inicio, fim)
    assert fatias == [{"label": "b3/app-trader-web", "value": 2, "pct": 100.0}]


def test_run_sem_origem_declarada_fica_fora_do_recorte(ws):
    """Sem declaração não há como adivinhar quem chamou — e inventar seria
    pior que a ausência."""
    conn = connect(ws)
    _grava(ws, conn, "github-31", "b3/e2e-web", None, "failure", 1)
    _, inicio, fim = _janela()
    assert por_origem(conn, *_janela()) == []
    assert erros_por_origem(conn, inicio, fim) == []


def test_o_painel_expoe_os_dois_recortes(suite_compartilhada):
    ws, _ = suite_compartilhada
    with logged_in_client(ws) as client:
        corpo = client.get("/api/v1/ci/observability?days=30").json()
        # um repositório de teste só...
        assert [r["name"] for r in corpo["by_repo"]] == ["b3/e2e-web"]
        # ...e dois produtos atrás dele
        assert len(corpo["by_origin"]) == 2
        assert corpo["errors_by_origin"][0]["label"] == "b3/app-trader-web"
