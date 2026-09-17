"""Limpar tudo — com o tamanho do estrago na frente (change 0192).

"Limpar tudo" é a operação em que o produto mais precisa ser confiável: quem
a usa costuma estar irritado com um dado errado, e é exatamente aí que se
apaga o que não devia. Duas defesas, e as duas são testadas aqui: a prévia
diz o tamanho ANTES de qualquer confirmação, e o removido vai para a
lixeira, não para o apagador.
"""

from __future__ import annotations

import pytest
import yaml

from arbites import ci_cobertura, ci_ingest, ci_retencao
from arbites.indexer import connect


@pytest.fixture
def conn(ws):
    return connect(ws)


def _semear(ws, conn, quantos: int = 3, com_anexo: bool = True):
    from arbites.indexer import reindex_file

    for i in range(1, quantos + 1):
        arquivos = {"log.txt": b"saida do teste"} if com_anexo else {}
        manifesto = {"version": 2, "signals": [],
                     "attachments": [{"kind": "log", "path": "log.txt"}]
                     if com_anexo else []}
        gravado = ci_ingest.escrever_run(
            ws.root,
            {"key": f"github-{i}", "provider": "github", "repo": "org/t",
             "workflow": "Regression", "run_id": str(i),
             "conclusion": "success",
             "started_at": f"2026-09-0{i}T10:00:00+00:00",
             "ingested_at": "2026-09-17T10:00:00+00:00"},
            manifesto, arquivos, None,
        )
        reindex_file(ws, conn, ws.root / gravado["path"])


# --- a prévia ---------------------------------------------------------------


def test_a_previa_diz_o_tamanho_antes_de_qualquer_confirmacao(ws, conn):
    """Uma confirmação que não diz quantas execuções vão embora não é
    confirmação, é um obstáculo."""
    _semear(ws, conn, quantos=3)

    previa = ci_retencao.previa_total(ws)

    assert previa["runs"] == 3
    assert previa["attachments"] == 3
    assert previa["bytes"] > 0
    assert previa["oldest"] < previa["newest"]


def test_previa_com_nada_ingerido_responde_zero_sem_quebrar(ws):
    previa = ci_retencao.previa_total(ws)

    assert previa["runs"] == 0 and previa["oldest"] is None


def test_a_previa_nao_apaga_nada(ws, conn):
    _semear(ws, conn, quantos=2)

    ci_retencao.previa_total(ws)

    assert len(list((ws.root / "ci").rglob("*.md"))) == 2


# --- a limpeza --------------------------------------------------------------


def test_limpar_leva_tudo_para_a_lixeira_nao_para_o_apagador(ws, conn):
    """Quem limpa costuma estar irritado — é aí que se apaga o que não
    devia. A lixeira é a segunda defesa."""
    _semear(ws, conn, quantos=2)

    ci_retencao.limpar_tudo(ws, conn)

    assert list((ws.root / "ci").rglob("*.md")) == []
    na_lixeira = list((ws.root / ".arbites" / "trash").rglob("*.md"))
    assert len(na_lixeira) == 2


def test_o_indice_esquece_junto(ws, conn):
    _semear(ws, conn, quantos=2)

    ci_retencao.limpar_tudo(ws, conn)

    assert ci_ingest.listar_runs(conn) == []


def test_a_cobertura_vai_junto(ws, conn):
    """Manter a cobertura afirmaria que o período já foi varrido quando não
    há mais nada dele no disco — e a próxima busca não traria nada de volta."""
    fonte = {"provider": "github", "repo": "org/t", "workflow": None}
    _semear(ws, conn, quantos=1)
    ci_cobertura.registrar(ws, fonte, "2026-01-01", "2026-09-01")

    ci_retencao.limpar_tudo(ws, conn)

    assert ci_cobertura.cobertura_da_fonte(ws, fonte) == []


def test_limpar_sem_nada_ingerido_nao_quebra(ws, conn):
    assert ci_retencao.limpar_tudo(ws, conn)["removed"]["runs"] == 0


def test_o_que_some_e_o_dado_nao_a_configuracao(ws, conn):
    """Limpar para reconferir e perder as origens declaradas obrigaria a
    reconfigurar tudo — e ninguém espera isso de uma limpeza de dados."""
    config = ws.config()
    config["observability"] = {"sources": [{"provider": "github",
                                            "repo": "org/t"}]}
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8")
    _semear(ws, conn, quantos=1)

    ci_retencao.limpar_tudo(ws, conn)

    assert ws.config()["observability"]["sources"][0]["repo"] == "org/t"


# --- quem pode ---------------------------------------------------------------


def test_apagar_tudo_e_coisa_de_admin(anon_client):
    """Mesmo alcance da limpeza por retenção, e mais consequência: esta não
    é seletiva."""
    from arbites import auth as auth_ops

    auth_ops.create_user(anon_client.app.state.auth, "editor@arbites.test",
                         "senha-de-editor-9", role="editor", status="active")
    anon_client.post("/api/v1/auth/login", json={
        "email": "editor@arbites.test", "password": "senha-de-editor-9"})

    resposta = anon_client.post("/api/v1/ci/purge")

    assert resposta.status_code == 403
    assert resposta.json()["error"]["code"] == "forbidden"
