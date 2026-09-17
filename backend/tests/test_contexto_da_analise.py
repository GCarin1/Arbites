"""Quanto texto a análise manda ao modelo (change 0198).

"Quero saber qual o tamanho do contexto que está sendo passado para a IA; se
for muito será muito chato de API." A pergunta é justa e não tinha resposta
na tela: quem clicava em Analisar não fazia ideia se aquilo custava um décimo
de centavo ou dez.

A boa notícia é estrutural, e estes testes a fixam: o dossiê é AGREGADO.
Dobrar as execuções não dobra o texto. O que cresce é a variedade — cenários
instáveis, repositórios —, e é nela que os tetos ficam.
"""

from __future__ import annotations

from arbites import ci_analise


def _painel(runs: int = 45, flaky: int = 0, repos: int = 1,
            mudancas: int = 0) -> dict:
    return {
        "period": {"since": "2026-08-18T00:00:00+00:00",
                   "until": "2026-09-17T00:00:00+00:00", "days": 30},
        "health": {"runs": runs, "success_rate": 78.1, "conclusive_runs": 32},
        "signals": [{"name": "duracao_min", "unit": "min", "current": 27.0,
                     "points": [{"value": 1.0}] * runs}],
        "flaky": [{"scenario": f"Cenário instável número {i}",
                   "testcase_id": f"CT-{i:04d}", "runs": 10, "failures": 4,
                   "flips": 7 - (i % 5), "newly_flaky": i % 3 == 0}
                  for i in range(flaky)],
        "findings": {"total": 1367, "by_impact": [], "top_rules": [],
                     "by_wcag": []},
        "distribution": {"runs_by_conclusion": []},
        "by_repo": [{"name": f"org/repo-{i}", "runs": 10, "failures": 2,
                     "success_rate": 80.0} for i in range(repos)],
        "by_origin": [],
        "errors_by_origin": [],
        "by_label": {},
        "changes": [{"text": f"algo mudou na medida {i}"}
                    for i in range(mudancas)],
    }


def test_o_tamanho_e_respondido_antes_de_analisar():
    t = ci_analise.tamanho_do_contexto(_painel())

    assert t["chars"] > 0
    assert t["tokens_aprox"] == round(t["chars"] / ci_analise.CHARS_POR_TOKEN)


def test_dobrar_as_execucoes_nao_dobra_o_texto():
    """O dossiê é agregado — é esta propriedade que torna o custo previsível,
    e ela precisa de prova, não de promessa."""
    poucas = ci_analise.tamanho_do_contexto(_painel(runs=45))["chars"]
    muitas = ci_analise.tamanho_do_contexto(_painel(runs=4500))["chars"]

    assert muitas < poucas * 1.2


def test_a_lista_de_instaveis_tem_teto():
    """Num dia ruim de uma suíte grande, essa lista sozinha passaria de tudo
    o mais somado — e o que a análise precisa dela são os piores."""
    d = ci_analise.dossie(_painel(flaky=300))

    assert len(d["flaky"]) == ci_analise.TETO_FLAKY
    assert d["flaky_total"] == 300  # o total continua dito


def test_o_teto_guarda_os_piores_e_os_novos_primeiro():
    """Cortar os 15 primeiros da lista crua entregaria quinze quaisquer."""
    d = ci_analise.dossie(_painel(flaky=60))

    assert d["flaky"][0]["newly_flaky"] is True
    viradas = [f["flips"] for f in d["flaky"] if f["newly_flaky"]]
    assert viradas == sorted(viradas, reverse=True)


def test_os_recortes_de_repositorio_tem_teto():
    d = ci_analise.dossie(_painel(repos=200))

    assert len(d["by_repo"]) == ci_analise.TETO_RECORTE


def test_com_teto_o_texto_para_de_crescer():
    normal = ci_analise.tamanho_do_contexto(_painel(flaky=10, repos=3))["chars"]
    absurdo = ci_analise.tamanho_do_contexto(
        _painel(flaky=500, repos=500, mudancas=500))["chars"]

    # Cresce, porque mais variedade é mais informação — mas de forma limitada,
    # não proporcional.
    assert absurdo < normal * 4
