"""Onde doer — a área de consulta do fim da Observabilidade (change 0197).

"Quero ter essas informações a partir de filtro: qual cenário falhou mais,
menos, quais os principais erros." Nenhuma dessas se respondia sem abrir
execução por execução — e a mensagem que responde "por que falhou?" já vinha
no relatório Cucumber e era descartada na leitura.
"""

from __future__ import annotations

import json

import pytest

from arbites import ci_ingest
from arbites.indexer import connect, reindex_file
from arbites.integrations_file import ler_cucumber


@pytest.fixture
def conn(ws):
    return connect(ws)


def _cucumber(cenarios: list[tuple[str, str, str | None]]) -> bytes:
    """(nome, status, mensagem de erro)"""
    return json.dumps([{
        "name": "Feature",
        "elements": [
            {"name": nome, "tags": [], "status": status,
             "steps": [{"result": {
                 "status": status,
                 **({"error_message": erro} if erro else {})}}]}
            for nome, status, erro in cenarios
        ],
    }]).encode("utf-8")


def _gravar(ws, conn, chave, cenarios, repo="org/testes", dia=10, jobs=None):
    gravado = ci_ingest.escrever_run(
        ws.root,
        {"key": chave, "provider": "github", "repo": repo,
         "workflow": "Regression", "run_id": chave, "conclusion": "failure",
         "started_at": f"2026-09-{dia:02d}T03:00:00+00:00",
         "finished_at": f"2026-09-{dia:02d}T03:20:00+00:00",
         "ingested_at": "2026-09-17T10:00:00+00:00",
         "jobs": jobs or []},
        {"version": 2, "signals": [],
         "attachments": [{"kind": "cucumber", "path": "results.json"}]},
        {"results.json": _cucumber(cenarios)}, None,
    )
    reindex_file(ws, conn, ws.root / gravado["path"])


# --- a mensagem que já vinha e era descartada -------------------------------


def test_a_mensagem_do_passo_que_falhou_e_lida():
    cenarios = ler_cucumber(_cucumber([
        ("Login", "failed", "AssertionError: esperado 3, recebido 4\n  at foo.js:1"),
    ]))

    assert cenarios[0]["error"].startswith("AssertionError: esperado 3")
    # Só a primeira linha: o resto é pilha de chamada, que agrupa mal e não
    # cabe numa tabela.
    assert "foo.js" not in cenarios[0]["error"]


def test_cenario_que_passou_nao_carrega_erro():
    cenarios = ler_cucumber(_cucumber([("Login", "passed", None)]))

    assert cenarios[0]["error"] is None


# --- o molde, que é o que permite agrupar -----------------------------------


def test_mensagens_iguais_com_numeros_diferentes_caem_no_mesmo_molde():
    """Agrupar pelo texto cru produziria uma lista de linhas únicas — que é o
    mesmo que não agrupar."""
    a = ci_ingest.molde_do_erro("esperado 3, recebido 4")
    b = ci_ingest.molde_do_erro("esperado 7, recebido 91")

    assert a == b


@pytest.mark.parametrize("ruido", [
    "timeout de 3000ms em https://app.exemplo/x",
    "timeout de 250ms em https://app.exemplo/y",
])
def test_tempo_e_endereco_saem_do_molde(ruido):
    assert "<tempo>" in ci_ingest.molde_do_erro(ruido)
    assert "<url>" in ci_ingest.molde_do_erro(ruido)


def test_mensagem_vazia_nao_vira_molde():
    assert ci_ingest.molde_do_erro("") is None
    assert ci_ingest.molde_do_erro(None) is None


# --- as perguntas -----------------------------------------------------------


def test_qual_cenario_falhou_mais(ws, conn):
    _gravar(ws, conn, "r1", [("Login", "failed", "erro A"),
                             ("Extrato", "passed", None)], dia=10)
    _gravar(ws, conn, "r2", [("Login", "failed", "erro A"),
                             ("Extrato", "passed", None)], dia=11)
    _gravar(ws, conn, "r3", [("Login", "passed", None),
                             ("Extrato", "failed", "erro B")], dia=12)

    d = ci_ingest.diagnostico(ws, conn, dias=365)

    pior = d["scenarios"]["mais_falharam"][0]
    assert pior["scenario"] == "Login"
    assert (pior["falhas"], pior["total"], pior["taxa_falha"]) == (2, 3, 66.7)


def test_quem_nunca_falhou_precisa_de_historico(ws, conn):
    """Um cenário que rodou uma vez e passou não provou estabilidade nenhuma;
    listá-lo como "sempre passou" seria dar um atestado que ele não tem."""
    for i, dia in enumerate((10, 11, 12), start=1):
        _gravar(ws, conn, f"r{i}", [("Sempre verde", "passed", None)], dia=dia)
    _gravar(ws, conn, "r9", [("Rodou uma vez", "passed", None)], dia=13)

    estaveis = ci_ingest.diagnostico(ws, conn, dias=365)["scenarios"]["nunca_falharam"]

    assert [c["scenario"] for c in estaveis] == ["Sempre verde"]


def test_qual_erro_mais_se_repete(ws, conn):
    _gravar(ws, conn, "r1", [("A", "failed", "esperado 1, recebido 2")], dia=10)
    _gravar(ws, conn, "r2", [("B", "failed", "esperado 5, recebido 9")], dia=11)
    _gravar(ws, conn, "r3", [("C", "failed", "elemento não encontrado")], dia=12)

    erros = ci_ingest.diagnostico(ws, conn, dias=365)["errors"]

    assert erros[0]["count"] == 2
    assert erros[0]["cenarios"] == 2  # o mesmo defeito em dois cenários
    assert erros[0]["exemplo"].startswith("esperado")


def test_qual_etapa_do_pipeline_quebra_mais(ws, conn):
    jobs = [{"name": "e2e", "conclusion": "failure"},
            {"name": "lint", "conclusion": "success"}]
    _gravar(ws, conn, "r1", [("A", "passed", None)], dia=10, jobs=jobs)
    _gravar(ws, conn, "r2", [("A", "passed", None)], dia=11, jobs=jobs)

    etapas = ci_ingest.diagnostico(ws, conn, dias=365)["jobs"]

    assert [(j["name"], j["falhas"]) for j in etapas] == [("e2e", 2)]


def test_o_filtro_de_repositorio_recorta_de_verdade(ws, conn):
    """Com mais de um repositório de teste, a lista global mistura times que
    não se conhecem — e o plano de correção é de um deles."""
    _gravar(ws, conn, "r1", [("Front", "failed", "x")], repo="org/front", dia=10)
    _gravar(ws, conn, "r2", [("Back", "failed", "y")], repo="org/back", dia=11)

    so_front = ci_ingest.diagnostico(ws, conn, dias=365, repo="org/front")

    assert [c["scenario"] for c in so_front["scenarios"]["mais_falharam"]] == ["Front"]
    assert set(so_front["repos"]) == {"org/front", "org/back"}


def test_periodo_sem_nada_responde_vazio_sem_quebrar(ws, conn):
    d = ci_ingest.diagnostico(ws, conn, dias=30)

    assert d["scenarios"]["mais_falharam"] == []
    assert d["errors"] == []
