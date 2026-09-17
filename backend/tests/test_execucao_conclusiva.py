"""Cancelada não é falha, e skipped nem rodou (change 0191).

25 verdes em 45 execuções apareciam como "55.6% de sucesso". A conta estava
certa e a pergunta, errada: das 45, 12 foram canceladas e 1 pulada. Nenhuma
das 13 disse nada sobre o produto — alguém apertou o botão, ou um push novo
substituiu a fila.

A verdade era 25 de 32: 78.1%. A diferença entre 55% e 78% é a diferença
entre uma suíte que parece quebrada e uma que parece saudável, e quem decide
onde investir a semana olha para esse número.
"""

from __future__ import annotations

import pytest

from arbites import ci_ingest
from arbites.ci_ingest import taxa_de_sucesso
from arbites.indexer import connect


@pytest.fixture
def conn(ws):
    return connect(ws)


# --- a conta ---------------------------------------------------------------


def test_o_caso_real_25_de_45_e_781_nao_556():
    conclusoes = (["success"] * 25 + ["failure"] * 7
                  + ["cancelled"] * 12 + ["skipped"])

    taxa, conclusivas, fora = taxa_de_sucesso(conclusoes)

    assert (taxa, conclusivas, fora) == (78.1, 32, 13)


def test_estourar_o_tempo_e_falhar_e_conta_como_tal():
    """`timed_out` fica DENTRO: estourar o tempo é falhar, com um motivo."""
    taxa, conclusivas, fora = taxa_de_sucesso(["success", "timed_out"])

    assert (taxa, conclusivas, fora) == (50.0, 2, 0)


@pytest.mark.parametrize("conclusion", ["cancelled", "skipped", "neutral",
                                        "action_required", "stale", None, ""])
def test_o_que_nao_deu_veredito_fica_fora(conclusion):
    assert not ci_ingest.e_conclusiva(conclusion)


def test_periodo_so_de_canceladas_nao_tem_taxa_em_vez_de_ter_zero():
    """0% diria que tudo quebrou; a verdade é que nada foi medido — e as duas
    levam a decisões opostas."""
    taxa, conclusivas, fora = taxa_de_sucesso(["cancelled", "skipped"])

    assert taxa is None and conclusivas == 0 and fora == 2


def test_sem_execucao_nenhuma_tambem_nao_tem_taxa():
    assert taxa_de_sucesso([])[0] is None


# --- no painel --------------------------------------------------------------


def _semear(ws, conn, conclusoes: list[str]):
    """Escreve runs direto no disco e indexa — o caminho de verdade."""
    from arbites.indexer import reindex_file

    for i, conclusao in enumerate(conclusoes, start=1):
        gravado = ci_ingest.escrever_run(
            ws.root,
            {"key": f"github-{i}", "provider": "github", "repo": "org/testes",
             "workflow": "Regression", "run_id": str(i),
             "conclusion": conclusao,
             "started_at": f"2026-09-0{(i % 9) + 1}T10:00:00+00:00",
             "ingested_at": "2026-09-17T10:00:00+00:00"},
            {"version": 2, "signals": [], "attachments": []}, {}, None,
        )
        reindex_file(ws, conn, ws.root / gravado["path"])


def test_a_taxa_do_painel_ignora_cancelada_e_skipped(ws, conn):
    _semear(ws, conn, ["success"] * 3 + ["failure"] + ["cancelled"] * 4)

    saude = ci_ingest.painel(ws, conn, dias=365)["health"]

    assert saude["success_rate"] == 75.0     # 3 de 4, não 3 de 8
    assert saude["runs"] == 8                # o total continua sendo 8
    assert saude["conclusive_runs"] == 4
    assert saude["inconclusive_runs"] == 4


def test_a_pizza_mostra_o_veredito_e_diz_quem_ficou_de_fora(ws, conn):
    """Sair da conta não é sair da tela: um total que não bate com o card ao
    lado, sem explicação, parece defeito."""
    _semear(ws, conn, ["success", "failure", "cancelled", "skipped"])

    divisao = ci_ingest.painel(ws, conn, dias=365)["distribution"]

    assert {f["label"] for f in divisao["runs_by_conclusion"]} == {
        "success", "failure"}
    assert {f["label"] for f in divisao["runs_inconclusive"]} == {
        "cancelled", "skipped"}
    assert divisao["inconclusive_total"] == 2


def test_falhas_por_repositorio_deixa_de_somar_o_que_nao_falhou(ws, conn):
    """A tabela dizia 20 falhas onde havia 7: "tudo que não passou" e "o que
    falhou" são coisas diferentes."""
    _semear(ws, conn, ["success"] * 2 + ["failure"] * 3 + ["cancelled"] * 5)

    linha = ci_ingest.painel(ws, conn, dias=365)["by_repo"][0]

    assert linha["failures"] == 3
    assert linha["runs"] == 10
    assert linha["conclusive"] == 5
    assert linha["inconclusive"] == 5
    assert linha["success_rate"] == 40.0
