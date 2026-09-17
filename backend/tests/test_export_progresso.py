"""O contrato que a barra de progresso consome (change 0193).

A barra só pode dizer QUANTO falta se o servidor disser o tamanho; sem isso
ela vira indeterminada, e inventar uma porcentagem seria mentir. E o arquivo
só chega com o nome certo se o servidor sugerir um — salvar como
`download.bin` obriga a renomear à mão todo export.

Estes testes fixam as duas coisas do lado que as promete.
"""

from __future__ import annotations

import pytest

from arbites import ci_ingest
from arbites.indexer import connect, reindex_file

FORMATOS = ["pdf", "csv", "md", "findings"]


@pytest.fixture
def com_dado(ws):
    conn = connect(ws)
    gravado = ci_ingest.escrever_run(
        ws.root,
        {"key": "github-1", "provider": "github", "repo": "org/t",
         "workflow": "Regression", "run_id": "1", "conclusion": "success",
         "started_at": "2026-09-10T03:00:00+00:00",
         "ingested_at": "2026-09-17T10:00:00+00:00"},
        {"version": 2, "signals": [], "attachments": []}, {}, None,
    )
    reindex_file(ws, conn, ws.root / gravado["path"])
    return ws


@pytest.mark.parametrize("formato", FORMATOS)
def test_o_tamanho_vem_no_cabecalho(client, com_dado, formato):
    """Sem `Content-Length` a barra não tem como dizer quanto falta."""
    resposta = client.get(
        f"/api/v1/ci/observability/export?format={formato}&days=30")

    assert resposta.status_code == 200
    assert int(resposta.headers["content-length"]) == len(resposta.content)


@pytest.mark.parametrize("formato", FORMATOS)
def test_o_nome_do_arquivo_vem_sugerido(client, com_dado, formato):
    """Salvar como `download.bin` obriga a renomear à mão todo export."""
    resposta = client.get(
        f"/api/v1/ci/observability/export?format={formato}&days=30")

    disposicao = resposta.headers["content-disposition"]
    assert disposicao.startswith("attachment;")
    assert 'filename="' in disposicao


def test_exportar_periodo_sem_dado_ainda_produz_arquivo(client):
    """Um período vazio é uma resposta legítima — e um export que falha aí
    parece defeito no meio de uma apresentação."""
    resposta = client.get("/api/v1/ci/observability/export?format=md&days=30")

    assert resposta.status_code == 200
    assert resposta.content
