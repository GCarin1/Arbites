"""Exportar o painel de observabilidade (change 0174).

Três formatos porque são três perguntas: a série crua para a planilha (csv),
o painel em texto para ata e wiki (md), e o painel COM os gráficos para
anexar (pdf). O gráfico é o ponto do PDF: um relatório de observabilidade sem
a linha do tempo é um retrato, que é o que esta aba existe para não ser.
"""

import pytest
from conftest import logged_in_client

from arbites import export_obs

PAINEL = {
    "period": {"since": "2026-08-17T00:00:00+00:00",
               "until": "2026-09-16T00:00:00+00:00", "days": 30},
    "previous": {"since": "2026-07-18T00:00:00+00:00",
                 "until": "2026-08-17T00:00:00+00:00"},
    "health": {"runs": 28, "runs_previous": 21, "success_rate": 78.6,
               "success_rate_previous": 95.0, "goal": 95,
               "last_run_at": "2026-09-16T03:00:00+00:00",
               "days_since_last_run": 0},
    "changes": [{"text": "qa-nightly.yml quebrou", "kind": "bad"},
                {"text": "CT-0004 virou instavel", "kind": "bad"}],
    "flaky": [{"scenario": "exporta extrato em PDF", "testcase_id": "CT-0004",
               "runs": 28, "failures": 5, "flips": 9, "newly_flaky": True}],
    "signals": [
        {"name": "lcp_ms", "kind": "performance", "unit": "ms",
         "current": 2612.0, "average": 2380.0, "previous_average": 2100.0,
         "delta_pct": 13.3, "direction": "lower", "goal": 2500,
         "points": [
             {"at": "2026-09-14T03:00:00+00:00", "value": 2400.0,
              "run_id": "github-9026", "conclusion": "success", "url": "u1"},
             {"at": "2026-09-15T03:00:00+00:00", "value": 2612.0,
              "run_id": "github-9027", "conclusion": "failure", "url": "u2"},
         ]},
        {"name": "cenarios_falhos", "kind": "suite", "unit": "cenarios",
         "current": 1.0, "average": 0.4, "previous_average": None,
         "delta_pct": None, "direction": None, "goal": None,
         "points": [{"at": "2026-09-15T03:00:00+00:00", "value": 1.0,
                     "run_id": "github-9027", "conclusion": "failure", "url": "u2"}]},
    ],
    "runs": [{"id": "github-9027", "workflow": "qa-nightly.yml",
              "conclusion": "failure", "started_at": "2026-09-15T03:00:00+00:00"}],
}


# -- CSV ---------------------------------------------------------------------

def test_csv_tem_uma_linha_por_medida_nao_por_sinal():
    """É o formato que a planilha filtra e agrupa sem ninguém desempilhar."""
    linhas = export_obs.sinais_csv(PAINEL).strip().splitlines()
    assert linhas[0].startswith("sinal,tipo,unidade,quando,valor,meta")
    assert len(linhas) == 1 + 3  # cabeçalho + 2 pontos de lcp + 1 de cenarios


def test_csv_carrega_a_execucao_que_produziu_cada_medida():
    """Sem o run a medida vira número solto: não dá para voltar à origem."""
    corpo = export_obs.sinais_csv(PAINEL)
    assert "github-9027" in corpo and "failure" in corpo


def test_csv_de_painel_vazio_ainda_traz_o_cabecalho():
    linhas = export_obs.sinais_csv({"signals": []}).strip().splitlines()
    assert len(linhas) == 1


# -- Markdown ----------------------------------------------------------------

def test_markdown_traz_saude_mudancas_instaveis_e_sinais():
    md = export_obs.painel_markdown(PAINEL)
    for secao in ("# Observabilidade", "## Saúde", "## O que mudou",
                  "## Testes instáveis", "## Sinais", "## Execuções recentes"):
        assert secao in md, secao
    assert "**28**" in md and "78.6%" in md and "meta 95%" in md
    assert "CT-0004" in md


def test_markdown_nao_afirma_melhora_sem_direcao_declarada():
    """"Subiu" não é "piorou": a direção é de quem instala (ADR 0016)."""
    md = export_obs.painel_markdown(PAINEL)
    assert "+13.3% vs. período anterior (piorou)" in md   # lcp_ms tem direction
    linha_cenarios = next(l for l in md.splitlines() if "cenarios_falhos" in l)
    assert "piorou" not in linha_cenarios and "melhorou" not in linha_cenarios


def test_markdown_de_painel_vazio_diz_o_que_faltou():
    md = export_obs.painel_markdown({})
    assert "Nada se moveu" in md
    assert "Nenhum sinal declarado chegou no período." in md
    assert "Nenhuma execução ingerida no período." in md


# -- PDF ---------------------------------------------------------------------

def test_pdf_sai_como_pdf_de_verdade():
    dados = export_obs.painel_pdf(PAINEL)
    assert dados[:4] == b"%PDF"
    assert len(dados) > 2000


def test_pdf_com_varias_mudancas_nao_estoura_a_largura():
    """O `multi_cell` do fpdf2 deixa o cursor à DIREITA da última linha: sem
    voltar à margem, o SEGUNDO parágrafo não tem espaço para um caractere e a
    exportação inteira falha. O defeito só aparece a partir do segundo item."""
    painel = {**PAINEL, "changes": [{"text": f"mudanca numero {i}"}
                                    for i in range(8)]}
    assert export_obs.painel_pdf(painel)[:4] == b"%PDF"


def test_pdf_de_painel_vazio_nao_quebra():
    """Instalação nova exporta um painel sem sinal nenhum."""
    assert export_obs.painel_pdf({})[:4] == b"%PDF"


def test_serie_constante_nao_divide_por_zero():
    """Todo ponto com o mesmo valor zera a amplitude do gráfico."""
    painel = {**PAINEL, "signals": [{
        "name": "constante", "unit": "x", "current": 5.0, "goal": None,
        "points": [{"at": f"2026-09-1{i}T03:00:00+00:00", "value": 5.0,
                    "conclusion": "success"} for i in range(1, 5)],
    }]}
    assert export_obs.painel_pdf(painel)[:4] == b"%PDF"


def test_numero_inteiro_sai_sem_casa_decimal():
    assert export_obs._numero(1.0) == "1"
    assert export_obs._numero(2612.0) == "2612"
    assert export_obs._numero(0.4) == "0.4"
    assert export_obs._numero(None) == "—"


# -- rota --------------------------------------------------------------------

@pytest.mark.parametrize("formato,tipo,extensao", [
    ("pdf", "application/pdf", ".pdf"),
    ("csv", "text/csv", ".csv"),
    ("md", "text/markdown", ".md"),
])
def test_a_rota_devolve_anexo_nos_tres_formatos(ws, formato, tipo, extensao):
    with logged_in_client(ws) as client:
        r = client.get(f"/api/v1/ci/observability/export?format={formato}&days=30")
        assert r.status_code == 200, r.text
        assert tipo in r.headers["content-type"]
        assert extensao in r.headers["content-disposition"]
        assert "attachment" in r.headers["content-disposition"]


def test_formato_desconhecido_e_recusado(ws):
    with logged_in_client(ws) as client:
        r = client.get("/api/v1/ci/observability/export?format=xlsx")
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "invalid_format"
