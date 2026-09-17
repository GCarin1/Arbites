"""As medidas que o Arbites calcula sobre a execução (ADR 0019, change 0194).

45 execuções ingeridas, 1367 violações de acessibilidade lidas, 405 cenários
extraídos — e "Sinais no tempo" vazio. A matéria-prima estava toda no disco,
e o eixo que faz um dashboard virar observabilidade não existia, porque a
tela esperava um `arbites.json` que o pipeline de outro time não publica.

A fronteira que estes testes guardam: reconhecer um formato documentado é
leitura; adivinhar o significado de um número solto é invenção. Só a primeira
vira sinal.
"""

from __future__ import annotations

import pytest

from arbites import ci_derivados, ci_ingest
from arbites.indexer import connect


@pytest.fixture
def conn(ws):
    return connect(ws)


def _meta(**extra):
    base = {
        "conclusion": "success",
        "started_at": "2026-09-10T03:00:00+00:00",
        "finished_at": "2026-09-10T03:12:30+00:00",
    }
    return {**base, **extra}


def _nomes(sinais):
    return {s["name"]: s["value"] for s in sinais}


# --- o que se sabe com certeza ----------------------------------------------


def test_a_duracao_sai_dos_horarios_do_provedor():
    """Em minutos, não segundos: uma suíte de regressão dura dezenas de
    minutos, e um eixo em milhares de segundos não se lê."""
    valores = _nomes(ci_derivados.derivar(_meta(), [], "2026-09-10T03:00:00+00:00"))

    assert valores["duracao_min"] == 12.5


def test_o_resultado_vira_um_ou_zero():
    passou = ci_derivados.derivar(_meta(), [], "x")
    falhou = _nomes(ci_derivados.derivar(_meta(conclusion="failure"), [], "x"))

    assert _nomes(passou)["resultado"] == 1.0
    assert falhou["resultado"] == 0.0
    # Sem unidade: "0/1" ao lado do número vira "0 0/1" no cartão.
    assert next(s for s in passou if s["name"] == "resultado")["unit"] is None


def test_cancelada_nao_vira_zero_no_grafico():
    """Zero é um ponto dizendo que quebrou; a verdade é que nada foi medido.
    É a mesma regra da change 0191, agora na série."""
    valores = _nomes(ci_derivados.derivar(_meta(conclusion="cancelled"), [], "x"))

    assert "resultado" not in valores


def test_os_cenarios_do_relatorio_viram_contagem_e_taxa():
    cenarios = ([{"status": "passed"}] * 7 + [{"status": "failed"}] * 3)

    valores = _nomes(ci_derivados.derivar(_meta(scenarios=cenarios), [], "x"))

    assert valores["cenarios"] == 10
    assert valores["cenarios_falhos"] == 3
    assert valores["cenarios_taxa"] == 70.0


def test_cenario_que_nao_provou_nada_conta_como_falho():
    """`blocked`, `undefined` e `pending` não são verdes; tratá-los como
    verdes infla a taxa exatamente onde ela precisa ser honesta."""
    cenarios = [{"status": "passed"}, {"status": "undefined"},
                {"status": "blocked"}]

    valores = _nomes(ci_derivados.derivar(_meta(scenarios=cenarios), [], "x"))

    assert valores["cenarios_falhos"] == 2


def test_a_acessibilidade_vira_serie_por_gravidade():
    achados = [
        {"impact": "critical", "count": 10, "wcag": "1.1.1"},
        {"impact": "serious", "count": 5, "wcag": "1.4.3"},
        {"impact": "minor", "count": 2, "wcag": "1.4.3"},
    ]

    valores = _nomes(ci_derivados.derivar(_meta(findings=achados), [], "x"))

    assert valores["acessibilidade_violacoes"] == 17
    assert valores["acessibilidade_critical"] == 10
    assert valores["acessibilidade_serious"] == 5
    assert valores["wcag_criterios_violados"] == 2


def test_jobs_falhos_saem_dos_jobs_do_provedor():
    jobs = [{"conclusion": "success"}, {"conclusion": "failure"},
            {"conclusion": "skipped"}]

    valores = _nomes(ci_derivados.derivar(_meta(jobs=jobs), [], "x"))

    assert valores["jobs_falhos"] == 1


# --- as três regras da ADR 0019 ---------------------------------------------


def test_sem_fonte_nao_ha_sinal_inventado():
    """Zero inventado é pior que ausência: zero é um ponto no gráfico,
    ausência não é."""
    valores = _nomes(ci_derivados.derivar(_meta(), [], "x"))

    assert "cenarios" not in valores
    assert "acessibilidade_violacoes" not in valores
    assert "jobs_falhos" not in valores


def test_o_nome_declarado_desliga_o_derivado_homonimo():
    """Quem produz sabe mais. O manifesto vence pelo NOME."""
    declarados = [{"name": "duracao_min", "value": 99.0, "kind": "custom"}]

    derivados = ci_derivados.derivar(_meta(), declarados, "x")

    assert "duracao_min" not in _nomes(derivados)


def test_todo_derivado_carrega_a_origem():
    """Um número calculado pelo Arbites apresentado como se o pipeline o
    tivesse medido seria uma mentira de procedência."""
    sinais = ci_derivados.derivar(_meta(scenarios=[{"status": "passed"}]), [], "x")

    assert sinais and all(s["source"] == "derivado" for s in sinais)
    assert all(s["kind"] == "derivado" for s in sinais)


def test_horario_ausente_ou_invertido_nao_vira_duracao_negativa():
    sem_fim = _nomes(ci_derivados.derivar(
        _meta(finished_at=None), [], "x"))
    invertido = _nomes(ci_derivados.derivar(
        _meta(finished_at="2026-09-10T02:00:00+00:00"), [], "x"))

    assert "duracao_min" not in sem_fim
    assert "duracao_min" not in invertido


# --- de ponta a ponta -------------------------------------------------------


def _gravar(ws, conn, chave="github-1", **extra):
    from arbites.indexer import reindex_file

    gravado = ci_ingest.escrever_run(
        ws.root,
        {"key": chave, "provider": "github", "repo": "org/t",
         "workflow": "Regression", "run_id": "1", "conclusion": "success",
         "started_at": "2026-09-10T03:00:00+00:00",
         "finished_at": "2026-09-10T03:20:00+00:00",
         "ingested_at": "2026-09-17T10:00:00+00:00", **extra},
        {"version": 2, "signals": [], "attachments": []}, {}, None,
    )
    reindex_file(ws, conn, ws.root / gravado["path"])
    return gravado


def test_a_serie_existe_sem_nenhum_manifesto(ws, conn):
    """O caso do relatório: nada declarado, e mesmo assim há o que olhar."""
    _gravar(ws, conn)

    sinais = ci_ingest.painel(ws, conn, dias=365)["signals"]

    assert {s["name"] for s in sinais} >= {"duracao_min", "resultado"}
    assert all(s["source"] == "derivado" for s in sinais)


def test_a_origem_chega_ate_o_painel(ws, conn):
    _gravar(ws, conn)

    sinais = ci_ingest.painel(ws, conn, dias=365)["signals"]

    assert sinais[0]["points"], "a série tem de ter ponto, não só nome"
    assert sinais[0]["source"] == "derivado"


def test_reprocessar_do_disco_cria_a_serie_do_que_ja_estava_ingerido(ws, conn):
    """Quem já tem execuções ingeridas não precisa rebuscar nada para ganhar
    a série — os anexos e os horários já estão aqui."""
    import frontmatter

    gravado = _gravar(ws, conn)
    caminho = ws.root / gravado["path"]
    post = frontmatter.load(caminho)
    post.metadata["signals"] = []          # como a versão anterior gravava
    post.metadata["attachments"] = [{"kind": "log", "path": "x"}]
    caminho.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")

    ci_ingest.reprocessar(ws, conn)

    nomes = {s["name"] for s in frontmatter.load(caminho).metadata["signals"]}
    assert "duracao_min" in nomes
