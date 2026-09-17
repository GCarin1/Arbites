"""Recortes e divisões do painel (change 0175).

Num projeto de micro-frontends a média global não é a saúde de nada: vários
componentes atrás de uma taxa só escondem exatamente o que se quer ver. E a
série responde "está piorando?", não "de que é feito o período" — a divisão
é outra pergunta, não um enfeite.
"""

from datetime import datetime, timedelta, timezone

import pytest
from conftest import logged_in_client

from arbites.ci_ingest import (
    MAX_VALORES_DE_ROTULO, achados, distribuicao, escrever_run,
    nomes_de_rotulo, por_repositorio, por_rotulo,
)
from arbites.indexer import connect, reindex_file

AGORA = datetime.now(timezone.utc)


def _grava(ws, conn, chave, repo, conclusao, dias_atras, rotulos=None,
           achados_=None, cenarios=None):
    quando = (AGORA - timedelta(days=dias_atras)).isoformat()
    run = {"key": chave, "provider": "github", "repo": repo,
           "workflow": "deploy-e2e.yml", "run_id": chave.split("-")[-1],
           "conclusion": conclusao, "started_at": quando,
           "ingested_at": quando, "event": "deployment"}
    manifesto = {"version": 2, "labels": rotulos or {},
                 "findings": achados_ or [], "attachments": []}
    gravado = escrever_run(ws.root, run, manifesto, {}, None)
    if cenarios:
        import frontmatter
        caminho = ws.root / gravado["path"]
        post = frontmatter.loads(caminho.read_text(encoding="utf-8"))
        post["scenarios"] = cenarios
        caminho.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    reindex_file(ws, conn, ws.root / gravado["path"])


@pytest.fixture()
def cenario(ws):
    """Dois repositórios com saúde diferente — o caso que a média esconde."""
    conn = connect(ws)
    for i in range(1, 5):
        _grava(ws, conn, f"github-10{i}", "b3/e2e-front",
               "success" if i > 2 else "failure", i,
               {"componente": "carteira-mfe", "ambiente": "hml"},
               [{"rule": "color-contrast", "impact": "serious", "wcag": "1.4.3",
                 "category": "accessibility", "count": 3, "page": "/carteira"},
                {"rule": "image-alt", "impact": "critical", "wcag": "1.1.1",
                 "category": "accessibility", "count": 1}],
               [{"scenario": "a", "status": "passed"},
                {"scenario": "b", "status": "failed" if i <= 2 else "passed"}])
    for i in range(1, 5):
        _grava(ws, conn, f"github-20{i}", "b3/e2e-api", "success", i,
               {"componente": "posicao-api", "ambiente": "hml"})
    return ws, conn


def test_cada_repositorio_tem_a_propria_taxa(cenario):
    ws, conn = cenario
    inicio_ant = (AGORA - timedelta(days=60)).isoformat()
    inicio = (AGORA - timedelta(days=30)).isoformat()
    fim = (AGORA + timedelta(days=1)).isoformat()
    linhas = {r["name"]: r for r in por_repositorio(conn, inicio_ant, inicio, fim)}
    assert linhas["b3/e2e-front"]["success_rate"] == 50.0
    assert linhas["b3/e2e-api"]["success_rate"] == 100.0


def test_o_pior_vem_primeiro(cenario):
    """Quem abre o painel quer saber onde dói."""
    _, conn = cenario
    inicio_ant = (AGORA - timedelta(days=60)).isoformat()
    inicio = (AGORA - timedelta(days=30)).isoformat()
    fim = (AGORA + timedelta(days=1)).isoformat()
    assert por_repositorio(conn, inicio_ant, inicio, fim)[0]["name"] == "b3/e2e-front"


def test_recorte_por_rotulo_do_manifesto(cenario):
    _, conn = cenario
    inicio_ant = (AGORA - timedelta(days=60)).isoformat()
    inicio = (AGORA - timedelta(days=30)).isoformat()
    fim = (AGORA + timedelta(days=1)).isoformat()
    linhas = {r["name"]: r for r in
              por_rotulo(conn, "componente", inicio_ant, inicio, fim)}
    assert linhas["carteira-mfe"]["success_rate"] == 50.0
    assert linhas["posicao-api"]["success_rate"] == 100.0


def test_rotulo_de_valor_unico_nao_e_recorte(cenario):
    """`ambiente` só tem 'hml' aqui: um valor não divide nada."""
    _, conn = cenario
    assert "componente" in nomes_de_rotulo(conn)
    assert "ambiente" not in nomes_de_rotulo(conn)


def test_rotulo_com_valores_demais_e_identificador_nao_recorte(ws):
    """`versao` com um valor por run empurraria `componente` para fora."""
    conn = connect(ws)
    for i in range(MAX_VALORES_DE_ROTULO + 3):
        _grava(ws, conn, f"github-30{i}", "b3/e2e-front", "success", i,
               {"versao": f"1.{i}.0", "componente": "carteira-mfe" if i % 2 else "ordens-mfe"})
    nomes = nomes_de_rotulo(conn)
    assert "componente" in nomes
    assert "versao" not in nomes


def test_divisao_do_periodo_por_resultado(cenario):
    _, conn = cenario
    inicio = (AGORA - timedelta(days=30)).isoformat()
    fim = (AGORA + timedelta(days=1)).isoformat()
    d = distribuicao(conn, inicio, fim)
    fatias = {f["label"]: f for f in d["runs_by_conclusion"]}
    assert fatias["success"]["value"] == 6 and fatias["failure"]["value"] == 2
    assert round(sum(f["pct"] for f in d["runs_by_conclusion"])) == 100


def test_a_porcentagem_vem_do_servidor(cenario):
    """Duas telas dividindo por conta própria discordam no arredondamento."""
    _, conn = cenario
    inicio = (AGORA - timedelta(days=30)).isoformat()
    fim = (AGORA + timedelta(days=1)).isoformat()
    for fatia in distribuicao(conn, inicio, fim)["scenarios_by_status"]:
        assert isinstance(fatia["pct"], float)


def test_achados_agregados_por_gravidade_regra_e_criterio(cenario):
    _, conn = cenario
    inicio_ant = (AGORA - timedelta(days=60)).isoformat()
    inicio = (AGORA - timedelta(days=30)).isoformat()
    fim = (AGORA + timedelta(days=1)).isoformat()
    a = achados(conn, inicio_ant, inicio, fim)
    assert a["total"] == 16          # 4 runs x (3 contraste + 1 alt)
    impacto = {f["label"]: f["value"] for f in a["by_impact"]}
    assert impacto == {"serious": 12, "critical": 4}
    assert a["top_rules"][0]["rule"] == "color-contrast"
    assert a["top_rules"][0]["wcag"] == "1.4.3"
    assert {c["wcag"] for c in a["by_wcag"]} == {"1.4.3", "1.1.1"}
    assert a["top_pages"][0]["page"] == "/carteira"


def test_o_painel_expoe_os_recortes_pela_rota(cenario):
    ws, _ = cenario
    with logged_in_client(ws) as client:
        corpo = client.get("/api/v1/ci/observability?days=30").json()
        assert len(corpo["by_repo"]) == 2
        assert "componente" in corpo["label_names"]
        assert corpo["findings"]["total"] == 16
        assert corpo["distribution"]["runs_by_conclusion"]
