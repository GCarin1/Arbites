"""O agente de análise da observabilidade (change 0179).

O painel responde perguntas isoladas — "está piorando?", "qual produto
quebra?", "onde estão as violações?". Ninguém junta as três no fim do dia.
O agente junta, escreve o veredito e **guarda**, para o histórico existir e
duas análises poderem ser comparadas.
"""

from datetime import datetime, timedelta, timezone

import pytest
from conftest import logged_in_client

from arbites import ci_analise
from arbites.ci_analise import (
    AnaliseError, AnaliseObservabilidade, ComparativoAnalises, dossie,
    dossie_markdown, listar, ler,
)

AGORA = datetime.now(timezone.utc)

PAINEL = {
    "period": {"since": "2026-08-17T00:00:00+00:00",
               "until": "2026-09-16T00:00:00+00:00", "days": 30},
    "health": {"runs": 96, "runs_previous": 80, "success_rate": 83.3,
               "success_rate_previous": 91.0, "goal": 95,
               "last_run_at": "2026-09-16T02:00:00+00:00",
               "days_since_last_run": 0},
    "changes": [{"text": "CT-0021 virou instável"}],
    "signals": [{"name": "lcp_ms", "unit": "ms", "current": 2633.0,
                 "average": 2400.0, "previous_average": 2100.0,
                 "delta_pct": 14.3, "goal": 2500, "direction": "lower",
                 "points": [{"at": "x", "value": 1.0}] * 24}],
    "flaky": [{"scenario": "atualiza cotacao", "testcase_id": "CT-0021",
               "runs": 24, "failures": 6, "flips": 9, "newly_flaky": True}],
    "findings": {"total": 1007, "previous_total": 900, "delta_pct": 11.9,
                 "by_impact": [{"label": "critical", "value": 482, "pct": 47.9}],
                 "top_rules": [{"rule": "color-contrast", "impact": "serious",
                                "wcag": "1.4.3", "count": 364}],
                 "by_wcag": [{"wcag": "1.4.3", "level": "AA", "count": 364}]},
    "distribution": {"runs_by_conclusion": [], "scenarios_by_status": []},
    "by_repo": [{"name": "b3/e2e-web", "runs": 48, "failures": 9,
                 "success_rate": 81.2, "delta_pct": None}],
    "by_origin": [{"name": "b3/app-trader-web", "runs": 24, "failures": 6,
                   "success_rate": 75.0, "delta_pct": -16.0}],
    "errors_by_origin": [{"label": "b3/app-trader-web", "value": 6, "pct": 37.5}],
    "by_label": {"componente": [{"name": "carteira-app", "runs": 24,
                                 "failures": 6, "success_rate": 75.0}]},
    "runs": [{"id": f"github-{i}"} for i in range(30)],
}


class ProviderFalso:
    """Devolve o modelo pedido sem rede. Guarda o prompt para conferência."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.system = None
        self.user = None

    def complete(self, system, user, modelo):
        self.system, self.user = system, user
        return self.resposta


def _analise(**kw):
    base = {"sintese": "A taxa caiu de 91% para 83,3%, abaixo da meta de 95%.",
            "saude_geral": "atencao",
            "riscos": [{"titulo": "LCP acima da meta", "evidencia": "2633 ms vs. 2500",
                        "gravidade": "media"}],
            "acoes": [{"acao": "Estabilizar CT-0021", "alvo": "carteira-app",
                       "porque": "9 viradas em 24 execuções"}],
            "acessibilidade": "482 achados críticos.",
            "observacao_por_produto": "b3/app-trader-web puxa a taxa para baixo."}
    return AnaliseObservabilidade(**{**base, **kw})


# -- dossiê ------------------------------------------------------------------

def test_o_dossie_e_recorte_e_nao_copia_do_painel():
    """Os 30 runs crus e os pontos de cada série pesariam megabytes por
    análise e não acrescentam nada ao comparativo, que é sobre agregado."""
    d = dossie(PAINEL)
    assert "runs" not in d                      # a lista crua fica de fora
    assert d["signals"][0]["points"] == 24      # só quantos, não quais
    assert d["health"]["success_rate"] == 83.3


def test_o_dossie_leva_os_dois_recortes_de_repositorio():
    d = dossie(PAINEL)
    assert d["by_origin"][0]["name"] == "b3/app-trader-web"
    assert d["by_repo"][0]["name"] == "b3/e2e-web"


def test_o_texto_marca_o_sinal_sem_direcao_declarada():
    """Sem direção o modelo não pode afirmar piora — e precisa ver isso."""
    painel = {**PAINEL, "signals": [{**PAINEL["signals"][0], "direction": None}]}
    texto = dossie_markdown(dossie(painel))
    assert "NÃO DECLARADA" in texto


def test_o_texto_destaca_instabilidade_nova():
    texto = dossie_markdown(dossie(PAINEL))
    assert "| SIM |" in texto                   # newly_flaky em destaque


def test_o_texto_traz_acessibilidade_com_criterio_wcag():
    texto = dossie_markdown(dossie(PAINEL))
    assert "1.4.3" in texto and "1007" in texto


# -- gravação e histórico ----------------------------------------------------

def test_a_analise_vira_artefato_do_workspace(ws):
    provider = ProviderFalso(_analise())
    saida = ci_analise.analisar(provider, ws, PAINEL, "meu-provider")
    caminho = ws.root / saida["path"]
    assert caminho.exists()
    assert saida["path"].startswith("ci/analises/ANL-")
    # o dossiê vai junto do veredito
    lida = ler(ws, saida["id"])
    assert lida["dossier"]["health"]["success_rate"] == 83.3
    assert "Síntese" in lida["body"]


def test_o_prompt_carrega_os_numeros_do_periodo(ws):
    provider = ProviderFalso(_analise())
    ci_analise.analisar(provider, ws, PAINEL, "p")
    assert "83.3" in provider.user and "b3/app-trader-web" in provider.user
    assert "Cite SEMPRE o número" in provider.system


def test_duas_analises_no_mesmo_dia_nao_colidem(ws):
    provider = ProviderFalso(_analise())
    a = ci_analise.analisar(provider, ws, PAINEL, "p")
    b = ci_analise.analisar(provider, ws, PAINEL, "p")
    assert a["id"] != b["id"]
    assert len(listar(ws)) == 2


def test_o_historico_vem_do_disco_e_sobrevive_ao_reindex(ws):
    """O histórico justifica decisão técnica: um reindex não pode apagá-lo."""
    provider = ProviderFalso(_analise())
    ci_analise.analisar(provider, ws, PAINEL, "p")
    from arbites.indexer import connect, reindex_full

    conn = connect(ws)
    reindex_full(ws, conn)
    (ws.arbites_dir / "index.db").unlink(missing_ok=True)
    assert len(listar(ws)) == 1


def test_o_historico_resume_sem_abrir_a_analise(ws):
    provider = ProviderFalso(_analise())
    ci_analise.analisar(provider, ws, PAINEL, "meu-provider")
    linha = listar(ws)[0]
    assert linha["saude_geral"] == "atencao"
    assert linha["runs"] == 96 and linha["success_rate"] == 83.3
    assert linha["findings_total"] == 1007 and linha["riscos"] == 1


def test_ler_analise_inexistente_e_404(ws):
    with pytest.raises(AnaliseError) as exc:
        ler(ws, "ANL-20260101-9")
    assert exc.value.status == 404


def test_id_com_traversal_e_recusado(ws):
    """`../../etc/passwd` não pode virar caminho de leitura."""
    with pytest.raises(AnaliseError) as exc:
        ler(ws, "../../etc/passwd")
    assert exc.value.code == "invalid_id"


# -- comparativo -------------------------------------------------------------

def _comparativo():
    return ComparativoAnalises(
        veredito="piorou", sintese="A taxa caiu.",
        melhoras=[], pioras=["taxa de sucesso"], permanece=["LCP acima da meta"],
        proximo_passo="Estabilizar CT-0021.")


def test_o_comparativo_vai_sempre_do_mais_velho_para_o_mais_novo(ws):
    """"Melhorou" depende de qual veio antes: deixar a direção com o chamador
    convidaria a inverter o veredito sem querer."""
    provider = ProviderFalso(_analise())
    antiga = ci_analise.analisar(provider, ws, PAINEL, "p")
    caminho = ws.root / antiga["path"]
    texto = caminho.read_text(encoding="utf-8").replace(
        antiga["created_at"], "2026-01-01T00:00:00+00:00")
    caminho.write_text(texto, encoding="utf-8")
    nova = ci_analise.analisar(provider, ws, PAINEL, "p")

    comparador = ProviderFalso(_comparativo())
    # ordem invertida de propósito
    saida = ci_analise.comparar(comparador, ws, nova["id"], antiga["id"])
    assert saida["from"] == antiga["id"] and saida["to"] == nova["id"]
    assert comparador.user.index("ANTERIOR") < comparador.user.index("MAIS RECENTE")


def test_o_comparativo_recebe_os_numeros_e_nao_so_o_texto(ws):
    """Comparar só o texto faria virar resenha de resenha."""
    provider = ProviderFalso(_analise())
    a = ci_analise.analisar(provider, ws, PAINEL, "p")
    b = ci_analise.analisar(provider, ws, PAINEL, "p")
    comparador = ProviderFalso(_comparativo())
    ci_analise.comparar(comparador, ws, a["id"], b["id"])
    assert comparador.user.count("Números que ela viu") == 2
    assert "83.3" in comparador.user


def test_comparar_uma_analise_com_ela_mesma_e_recusado(ws):
    provider = ProviderFalso(_analise())
    a = ci_analise.analisar(provider, ws, PAINEL, "p")
    with pytest.raises(AnaliseError) as exc:
        ci_analise.comparar(ProviderFalso(_comparativo()), ws, a["id"], a["id"])
    assert exc.value.code == "same_analysis"


# -- rotas -------------------------------------------------------------------

def test_periodo_sem_execucao_recusa_em_vez_de_analisar_o_vazio(ws):
    with logged_in_client(ws) as client:
        r = client.post("/api/v1/ci/analysis", json={"days": 30})
        assert r.status_code in (409, 422)
        # sem provider configurado responde 409; com provider, 422 no_runs
        assert r.json()["error"]["code"] in ("ai_disabled", "no_runs")


def test_o_historico_responde_vazio_numa_instalacao_nova(ws):
    with logged_in_client(ws) as client:
        r = client.get("/api/v1/ci/analysis")
        assert r.status_code == 200
        assert r.json() == {"analyses": []}
