"""Exportar o painel de observabilidade — CSV, Markdown e PDF (change 0174).

Três formatos porque são três perguntas diferentes, e um formato só atende
mal duas delas:

- **CSV** é a série crua, uma linha por medida. Serve para levar para a
  planilha e cruzar com o que o Arbites não conhece (custo, release, incidente).
- **Markdown** é o painel em texto: entra em ata de reunião, em issue, em wiki,
  e continua legível daqui a um ano sem nenhum leitor especial.
- **PDF** é o painel COM os gráficos, para anexar e mandar. A série desenhada
  é o ponto: um relatório de observabilidade sem a linha do tempo é um retrato,
  que é exatamente o que a aba existe para não ser (ADR 0016).

Os gráficos do PDF são desenhados aqui, com as primitivas do fpdf2, e não
capturados da tela: exportar não pode depender de haver um navegador aberto.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

# Paleta do PDF. Vermelho/azul são os mesmos papéis da tela (execução que
# falhou / que passou), para quem vê o anexo reconhecer o que já viu.
_AZUL = (56, 139, 253)
_VERMELHO = (218, 54, 51)
_CINZA = (140, 149, 159)
_TEXTO = (36, 41, 47)


def _latin1(texto: str) -> str:
    """A fonte core do fpdf2 é latin-1; o que não codifica vira '?'."""
    return str(texto).encode("latin-1", "replace").decode("latin-1")


def _quando(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(str(iso)).strftime("%d/%m/%Y")
    except ValueError:
        return str(iso)[:10]


def _numero(valor: Any) -> str:
    """`1.0 cenarios` é ruído: sinal inteiro sai inteiro, como na tela."""
    if valor is None:
        return "—"
    try:
        f = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    return str(int(f)) if f == int(f) else f"{f:g}"


def _direcao(sinal: dict[str, Any]) -> str:
    """"Subiu" não é "piorou": a direção é declarada por quem instala, e sem
    ela o texto não afirma melhora nem piora (ADR 0016)."""
    delta = sinal.get("delta_pct")
    if delta is None:
        return "sem base anterior"
    direcao = sinal.get("direction")
    if not direcao:
        return f"{delta:+.1f}% vs. período anterior"
    piorou = (delta > 0) if direcao == "lower" else (delta < 0)
    palavra = "piorou" if piorou else "melhorou"
    return f"{delta:+.1f}% vs. período anterior ({palavra})"


# -- CSV ---------------------------------------------------------------------


def sinais_csv(painel: dict[str, Any]) -> str:
    """Uma linha por MEDIDA, não por sinal: é o formato que a planilha sabe
    filtrar, agrupar e cruzar sem ninguém desempilhar nada antes."""
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\n")
    escritor.writerow([
        "sinal", "tipo", "unidade", "quando", "valor", "meta", "direcao",
        "execucao", "conclusao", "url",
    ])
    for sinal in painel.get("signals") or []:
        for ponto in sinal.get("points") or []:
            escritor.writerow([
                sinal.get("name"), sinal.get("kind"), sinal.get("unit"),
                ponto.get("at"), ponto.get("value"),
                sinal.get("goal") if sinal.get("goal") is not None else "",
                sinal.get("direction") or "",
                ponto.get("run_id"), ponto.get("conclusion"), ponto.get("url"),
            ])
    return saida.getvalue()


# -- Markdown ----------------------------------------------------------------


def painel_markdown(painel: dict[str, Any]) -> str:
    periodo = painel.get("period") or {}
    saude = painel.get("health") or {}
    linhas = [
        "# Observabilidade",
        "",
        f"Período de {_quando(periodo.get('since'))} a"
        f" {_quando(periodo.get('until'))} ({periodo.get('days')} dias),"
        " comparado com o período anterior de mesmo tamanho.",
        "",
        "## Saúde",
        "",
        f"- Execuções no período: **{saude.get('runs', 0)}**"
        f" (anterior: {saude.get('runs_previous', 0)})",
    ]
    taxa = saude.get("success_rate")
    if taxa is not None:
        meta = saude.get("goal")
        linhas.append(
            f"- Taxa de sucesso: **{taxa}%**"
            + (f" — meta {meta}%" if meta is not None else "")
        )
    linhas += [
        f"- Última execução: {_quando(saude.get('last_run_at'))}",
        "",
        "## O que mudou",
        "",
    ]
    mudancas = painel.get("changes") or []
    linhas += [f"- {m.get('text')}" for m in mudancas] or [
        "- Nada se moveu o bastante para merecer atenção neste período."
    ]

    instaveis = painel.get("flaky") or []
    linhas += ["", "## Testes instáveis", ""]
    if instaveis:
        linhas += [
            "| Cenário | Caso | Execuções | Falhas | Viradas | Novo |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
        linhas += [
            f"| {f.get('scenario')} | {f.get('testcase_id') or '—'} |"
            f" {f.get('runs')} | {f.get('failures')} | {f.get('flips')} |"
            f" {'sim' if f.get('newly_flaky') else 'não'} |"
            for f in instaveis
        ]
    else:
        linhas.append("Nenhum cenário passou e falhou no mesmo período.")

    linhas += ["", "## Sinais", ""]
    sinais = painel.get("signals") or []
    if sinais:
        linhas += [
            "| Sinal | Atual | Média | Meta | Variação | Pontos |",
            "| --- | ---: | ---: | ---: | --- | ---: |",
        ]
        for s in sinais:
            unidade = f" {s['unit']}" if s.get("unit") else ""
            linhas.append(
                f"| {s.get('name')} |"
                f" {s.get('current') if s.get('current') is not None else '—'}{unidade} |"
                f" {s.get('average') if s.get('average') is not None else '—'} |"
                f" {s.get('goal') if s.get('goal') is not None else '—'} |"
                f" {_direcao(s)} | {len(s.get('points') or [])} |"
            )
    else:
        linhas.append("Nenhum sinal declarado chegou no período.")

    runs = painel.get("runs") or []
    linhas += ["", "## Execuções recentes", ""]
    if runs:
        linhas += ["| Execução | Workflow | Conclusão | Quando |",
                   "| --- | --- | --- | --- |"]
        linhas += [
            f"| {r.get('id')} | {r.get('workflow')} |"
            f" {r.get('conclusion') or '—'} |"
            f" {_quando(r.get('started_at') or r.get('ingested_at'))} |"
            for r in runs[:30]
        ]
    else:
        linhas.append("Nenhuma execução ingerida no período.")
    return "\n".join(linhas) + "\n"


# -- PDF ---------------------------------------------------------------------


def _paragrafo(pdf, texto: str, altura: float = 4.5) -> None:
    """Um parágrafo que começa na margem esquerda.

    O `multi_cell` do fpdf2 deixa o cursor à DIREITA da última linha, então
    duas chamadas seguidas com largura 0 quebram na segunda: a primeira
    consome a linha e a segunda não tem espaço para um caractere sequer. O
    defeito só aparece quando há mais de um item — por isso o reset explícito.
    """
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, altura, _latin1(texto), new_x="LMARGIN", new_y="NEXT")


def _desenhar_serie(pdf, sinal: dict[str, Any], x: float, y: float,
                    largura: float, altura: float) -> None:
    """O gráfico do sinal, desenhado no PDF.

    Mesma leitura da tela: linha da série, ponto azul para execução que
    passou e vermelho para a que falhou, e a meta como tracejado — sem ela
    o número não diz se está aceitável.
    """
    pontos = [p for p in (sinal.get("points") or []) if p.get("value") is not None]
    if not pontos:
        pdf.set_xy(x, y + altura / 2)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*_CINZA)
        pdf.cell(largura, 4, _latin1("sem medida no período"), align="C")
        return

    valores = [float(p["value"]) for p in pontos]
    meta = sinal.get("goal")
    baixo, alto = min(valores), max(valores)
    if meta is not None:
        baixo, alto = min(baixo, float(meta)), max(alto, float(meta))
    if alto == baixo:                      # série constante não é linha reta no zero
        alto, baixo = alto + 1, baixo - 1
    escala = altura / (alto - baixo)
    passo = largura / max(len(valores) - 1, 1)

    def ponto_y(valor: float) -> float:
        return y + altura - (valor - baixo) * escala

    # moldura discreta, para o gráfico ter borda mesmo sem eixo desenhado
    pdf.set_draw_color(225, 228, 232)
    pdf.set_line_width(0.2)
    pdf.rect(x, y, largura, altura)

    if meta is not None:
        pdf.set_draw_color(*_CINZA)
        pdf.set_line_width(0.3)
        ym = ponto_y(float(meta))
        passo_tracejado = 3.0
        px = x
        while px < x + largura:
            pdf.line(px, ym, min(px + 1.6, x + largura), ym)
            px += passo_tracejado

    pdf.set_draw_color(*_AZUL)
    pdf.set_line_width(0.4)
    for i in range(len(valores) - 1):
        pdf.line(x + i * passo, ponto_y(valores[i]),
                 x + (i + 1) * passo, ponto_y(valores[i + 1]))

    for i, p in enumerate(pontos):
        falhou = p.get("conclusion") not in (None, "success")
        cor = _VERMELHO if falhou else _AZUL
        pdf.set_fill_color(*cor)
        pdf.set_draw_color(*cor)
        pdf.circle(x=x + i * passo - 0.7, y=ponto_y(float(p["value"])) - 0.7,
                   radius=0.7, style="F")


def painel_pdf(painel: dict[str, Any]) -> bytes:
    from fpdf import FPDF

    periodo = painel.get("period") or {}
    saude = painel.get("health") or {}
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.set_text_color(*_TEXTO)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, "Observabilidade", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_CINZA)
    pdf.cell(0, 5, _latin1(
        f"{_quando(periodo.get('since'))} a {_quando(periodo.get('until'))}"
        f" ({periodo.get('days')} dias), comparado com o periodo anterior"
    ), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # -- saúde: os três números do topo, na mesma ordem da tela
    pdf.set_text_color(*_TEXTO)
    cartoes = [
        ("Execucoes no periodo", str(saude.get("runs", 0)),
         f"{saude.get('runs_previous', 0)} no periodo anterior"),
        ("Taxa de sucesso",
         f"{saude['success_rate']}%" if saude.get("success_rate") is not None else "—",
         f"meta {saude['goal']}%" if saude.get("goal") is not None else "sem meta"),
        ("Ultima execucao", _quando(saude.get("last_run_at")),
         f"{saude.get('days_since_last_run')} dia(s) atras"
         if saude.get("days_since_last_run") is not None else "—"),
    ]
    largura = (pdf.w - 28) / 3
    topo = pdf.get_y()
    for i, (rotulo, valor, nota) in enumerate(cartoes):
        x = 14 + i * largura
        pdf.set_draw_color(225, 228, 232)
        pdf.rect(x, topo, largura - 3, 20)
        pdf.set_xy(x + 3, topo + 3)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*_CINZA)
        pdf.cell(largura - 6, 3, _latin1(rotulo.upper()))
        pdf.set_xy(x + 3, topo + 7)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*_TEXTO)
        pdf.cell(largura - 6, 7, _latin1(valor))
        pdf.set_xy(x + 3, topo + 15)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*_CINZA)
        pdf.cell(largura - 6, 3, _latin1(nota))
    pdf.set_y(topo + 25)

    def titulo(texto: str) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*_TEXTO)
        pdf.cell(0, 6, _latin1(texto), new_x="LMARGIN", new_y="NEXT")

    titulo("O que mudou")
    pdf.set_font("Helvetica", "", 9)
    mudancas = painel.get("changes") or []
    if mudancas:
        for m in mudancas:
            _paragrafo(pdf, f"- {m.get('text')}")
    else:
        pdf.set_text_color(*_CINZA)
        _paragrafo(pdf,
                   "Nada se moveu o bastante para merecer atencao neste periodo.")
    pdf.ln(3)

    # -- sinais: o gráfico é o ponto do documento
    titulo("Sinais no tempo")
    for sinal in painel.get("signals") or []:
        if pdf.get_y() > pdf.h - 45:
            pdf.add_page()
        y = pdf.get_y()
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_TEXTO)
        pdf.set_xy(14, y)
        pdf.cell(90, 5, _latin1(sinal.get("name") or ""))
        unidade = f" {sinal['unit']}" if sinal.get("unit") else ""
        atual = sinal.get("current")
        pdf.cell(
            0, 5,
            _latin1(f"{_numero(atual)}{unidade}" if atual is not None else "-"),
            align="R",
        )
        pdf.set_xy(14, y + 5)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*_CINZA)
        meta = sinal.get("goal")
        legenda = _direcao(sinal)
        if meta is not None:
            direcao = sinal.get("direction")
            sentido = (" (quanto menor, melhor)" if direcao == "lower"
                       else " (quanto maior, melhor)" if direcao == "higher" else "")
            legenda += f" · meta {_numero(meta)}{unidade}{sentido}"
        pdf.cell(0, 4, _latin1(legenda))
        _desenhar_serie(pdf, sinal, 14, y + 10, pdf.w - 28, 18)
        pdf.set_y(y + 31)

    instaveis = painel.get("flaky") or []
    if instaveis:
        if pdf.get_y() > pdf.h - 45:
            pdf.add_page()
        titulo("Testes instaveis")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*_CINZA)
        colunas = [("Cenario", 86), ("Caso", 24), ("Exec.", 16),
                   ("Falhas", 16), ("Viradas", 18), ("Novo", 16)]
        for rotulo, w in colunas:
            pdf.cell(w, 5, _latin1(rotulo))
        pdf.ln(5)
        pdf.set_font("Helvetica", "", 8)
        for f in instaveis:
            pdf.set_text_color(*_TEXTO)
            if pdf.get_y() > pdf.h - 20:
                pdf.add_page()
            valores = [
                str(f.get("scenario") or "")[:60], str(f.get("testcase_id") or "—"),
                str(f.get("runs")), str(f.get("failures")), str(f.get("flips")),
                "sim" if f.get("newly_flaky") else "nao",
            ]
            for (_, w), valor in zip(colunas, valores):
                pdf.cell(w, 5, _latin1(valor))
            pdf.ln(5)

    saida = pdf.output()
    return bytes(saida)
