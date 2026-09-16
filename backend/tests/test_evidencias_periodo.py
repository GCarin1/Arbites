"""Galeria de evidências do período (change 0180).

Até aqui a evidência só existia dentro da descida: para ver o print da falha
era preciso já saber em qual execução ela aconteceu — o que inverte a ordem
natural, porque muitas vezes é justamente o print que diz onde olhar.
"""

from datetime import datetime, timedelta, timezone

import pytest
from conftest import logged_in_client

from arbites.ci_ingest import escrever_run, evidencias
from arbites.indexer import connect, reindex_file

AGORA = datetime.now(timezone.utc)
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c6360000002000100ffff03000006000557bfabd4000000"
    "0049454e44ae426082")


def _grava(ws, conn, chave, conclusao, dias_atras, origem="b3/app-trader-web"):
    quando = (AGORA - timedelta(days=dias_atras)).isoformat()
    run = {"key": chave, "provider": "github", "repo": "b3/e2e-web",
           "workflow": "deploy-e2e.yml", "run_id": chave.split("-")[-1],
           "conclusion": conclusao, "started_at": quando, "ingested_at": quando}
    manifesto = {
        "version": 2,
        "trigger": {"repo": origem},
        "attachments": [
            {"kind": "screenshot", "path": "falha.png", "title": "Tela na falha"},
            {"kind": "log", "path": "suite.log", "title": "Log da suíte"},
        ],
    }
    arquivos = {"falha.png": PNG, "suite.log": b"linha\n" * 30}
    gravado = escrever_run(ws.root, run, manifesto, arquivos, None)
    reindex_file(ws, conn, ws.root / gravado["path"])


@pytest.fixture()
def periodo(ws):
    conn = connect(ws)
    _grava(ws, conn, "github-101", "failure", 1)
    _grava(ws, conn, "github-102", "success", 2)
    _grava(ws, conn, "github-103", "failure", 3, origem="b3/app-ordens-web")
    return ws, conn


def _janela(dias=30):
    return ((AGORA - timedelta(days=dias)).isoformat(),
            (AGORA + timedelta(days=1)).isoformat())


def test_a_evidencia_carrega_o_contexto_da_execucao(periodo):
    """Sem o run, um print solto não é evidência de nada."""
    _, conn = periodo
    item = evidencias(conn, *_janela())["items"][0]
    for campo in ("run_id", "workflow", "conclusion", "repo", "trigger_repo", "at"):
        assert item[campo], campo


def test_o_recorte_por_falha_e_o_que_se_usa(periodo):
    """O print de um run verde quase nunca é o que se procura."""
    _, conn = periodo
    inicio, fim = _janela()
    todas = evidencias(conn, inicio, fim)["items"]
    falhas = evidencias(conn, inicio, fim, so_falhas=True)["items"]
    assert len(todas) == 6 and len(falhas) == 4
    assert all(i["conclusion"] != "success" for i in falhas)


def test_filtra_por_tipo(periodo):
    _, conn = periodo
    inicio, fim = _janela()
    prints = evidencias(conn, inicio, fim, kind="screenshot")["items"]
    assert len(prints) == 3 and all(i["kind"] == "screenshot" for i in prints)


def test_filtra_por_repositorio_de_origem(periodo):
    """O recorte que responde "o que quebrou no deploy daquele produto"."""
    _, conn = periodo
    inicio, fim = _janela()
    itens = evidencias(conn, inicio, fim, origem="b3/app-ordens-web")["items"]
    assert itens and all(i["trigger_repo"] == "b3/app-ordens-web" for i in itens)


def test_mais_recente_primeiro(periodo):
    """Quem abre a aba está atrás do que acabou de quebrar."""
    _, conn = periodo
    itens = evidencias(conn, *_janela())["items"]
    datas = [i["at"] for i in itens]
    assert datas == sorted(datas, reverse=True)


def test_o_resumo_por_tipo_ignora_os_filtros(periodo):
    """Os contadores do seletor não podem encolher conforme se filtra: eles
    são o que diz o que existe para filtrar."""
    _, conn = periodo
    inicio, fim = _janela()
    tipos = {f["label"]: f["value"]
             for f in evidencias(conn, inicio, fim, kind="log")["by_kind"]}
    assert tipos == {"screenshot": 3, "log": 3}


def test_o_limite_e_anunciado(periodo):
    """Uma lista cortada em silêncio faz quem olha concluir que não há mais."""
    _, conn = periodo
    inicio, fim = _janela()
    assert evidencias(conn, inicio, fim, limite=2)["truncated"] is True
    assert evidencias(conn, inicio, fim)["truncated"] is False


def test_o_limite_tem_teto_proprio(periodo):
    """Um `limit` gigante na querystring não pode virar varredura da base."""
    _, conn = periodo
    inicio, fim = _janela()
    assert len(evidencias(conn, inicio, fim, limite=10_000)["items"]) == 6


def test_fora_do_periodo_nao_entra(periodo):
    ws, conn = periodo
    _grava(ws, conn, "github-999", "failure", 120)
    assert len(evidencias(conn, *_janela())["items"]) == 6


def test_a_rota_responde_com_os_filtros(periodo):
    ws, _ = periodo
    with logged_in_client(ws) as client:
        r = client.get("/api/v1/ci/evidences?days=30&kind=screenshot"
                       "&failures_only=true")
        assert r.status_code == 200, r.text
        corpo = r.json()
        assert len(corpo["items"]) == 2
        assert corpo["total_bytes"] > 0


def test_o_anexo_servido_nao_escapa_da_pasta_ci(periodo):
    """O caminho vem do índice, mas a contenção é conferida no disco: um
    índice adulterado não pode virar leitura de arquivo arbitrário."""
    ws, _ = periodo
    with logged_in_client(ws) as client:
        assert client.get(
            "/api/v1/ci/attachment?path=../arbites.yaml").status_code == 404
