"""Agente de análise da observabilidade: dossiê, veredito e histórico (0179).

O painel responde perguntas isoladas — "está piorando?", "qual produto
quebra?", "onde estão as violações?". Ninguém junta as três no fim do dia. Um
agente junta: lê o período inteiro, escreve o veredito e **guarda**.

## Três decisões que mandam neste arquivo

**1. A análise é ARTEFATO do workspace, não linha de tabela.**
`ci/analises/<id>.md`, com o dossiê no frontmatter e o veredito no corpo
(ADR 0001). Um reindex não pode apagar o histórico que justifica uma decisão
técnica, e o arquivo continua legível por humano e por `git diff`.

**2. O DOSSIÊ é guardado junto do veredito.**
Comparar duas análises exige comparar os números que cada uma viu — não só o
que a IA escreveu sobre eles. Guardar só o texto faria o comparativo virar
resenha de resenha, e no dia em que a retenção apagar os runs antigos nem o
texto teria com o que ser conferido.

**3. Comparar é perguntar de novo, com as duas na mão.**
Não se calcula "melhorou" no código: `success_rate` subiu e `lcp_ms` também
não diz se o produto está melhor. O comparativo entrega os dois dossiês e os
dois vereditos ao modelo e pede o julgamento — que é exatamente o que um
humano faria com as duas folhas lado a lado.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter
from pydantic import BaseModel, Field

PASTA = "ci/analises"


class AnaliseError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# -- o que o modelo devolve --------------------------------------------------


class RiscoDaAnalise(BaseModel):
    titulo: str
    evidencia: str = ""          # o número que sustenta o risco
    gravidade: str = "media"     # alta | media | baixa


class AcaoDaAnalise(BaseModel):
    acao: str
    alvo: str = ""               # repositório, componente ou cenário
    porque: str = ""


class AnaliseObservabilidade(BaseModel):
    """O veredito. Campos curtos de propósito: análise que ninguém lê não
    serve, e o dossiê inteiro já está guardado ao lado."""

    sintese: str = Field(description="o estado do período em 2 a 4 frases")
    saude_geral: str = Field(
        default="atencao",
        description="boa | atencao | ruim — o julgamento em uma palavra")
    riscos: list[RiscoDaAnalise] = []
    acoes: list[AcaoDaAnalise] = []
    acessibilidade: str = ""     # leitura específica dos achados de WCAG
    observacao_por_produto: str = ""   # o que diverge entre os repositórios


class ComparativoAnalises(BaseModel):
    veredito: str = Field(
        default="estavel",
        description="melhorou | piorou | estavel | misto")
    sintese: str
    melhoras: list[str] = []
    pioras: list[str] = []
    permanece: list[str] = []    # o que não se mexeu entre as duas
    proximo_passo: str = ""


_SISTEMA = (
    "Você analisa observabilidade de testes automatizados de um portfólio de"
    " micro-frontends, back-ends e aplicativos. Recebe um dossiê com números"
    " de um período: saúde, séries de sinais com meta e direção declaradas,"
    " cenários instáveis, achados de acessibilidade com critério WCAG, e o"
    " recorte por repositório de teste e por repositório de origem (a"
    " aplicação cujo deploy disparou a suíte).\n\n"
    "Regras:\n"
    "- Cite SEMPRE o número que sustenta cada afirmação. Sem número, não"
    " afirme.\n"
    "- Só diga que um sinal piorou ou melhorou quando o dossiê trouxer a"
    " direção declarada; sem ela, diga apenas que subiu ou desceu.\n"
    "- Instabilidade nova vale mais que instabilidade antiga: a primeira é"
    " notícia, a segunda o time já conhece.\n"
    "- Prefira apontar o repositório de ORIGEM ao de teste quando for falar"
    " de produto — um repositório de teste serve vários produtos.\n"
    "- Não invente causa raiz que o dossiê não sustente. 'Não dá para saber"
    " daqui' é uma resposta legítima.\n"
    "- Responda em português do Brasil."
)

_SISTEMA_COMPARATIVO = (
    "Você compara DUAS análises de observabilidade do mesmo produto, feitas"
    " em momentos diferentes. Recebe os dois dossiês (os números que cada uma"
    " viu) e os dois vereditos.\n\n"
    "Regras:\n"
    "- Compare os números, não as palavras: um texto mais otimista não é"
    " melhora.\n"
    "- Períodos de tamanhos diferentes não se comparam em valor absoluto;"
    " use taxa e diga que o fez.\n"
    "- Separe o que melhorou, o que piorou e o que NÃO se mexeu — o que ficou"
    " parado costuma ser o que ninguém pegou.\n"
    "- Se as duas análises não forem comparáveis (períodos sem sobreposição de"
    " repositórios, por exemplo), diga isso em vez de forçar um veredito.\n"
    "- Responda em português do Brasil."
)


# -- dossiê ------------------------------------------------------------------


def _numero(valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, float) and valor == int(valor):
        return str(int(valor))
    return str(valor)


# O dossiê é agregado: dobrar as execuções não dobra o texto. O que cresce é
# a variedade — cenários instáveis, repositórios, rótulos —, e é nela que os
# tetos ficam. Sem eles, um dia ruim numa suíte grande manda para o modelo uma
# lista de centenas de linhas que não muda a conclusão e custa em toda análise.
TETO_FLAKY = 15
TETO_RECORTE = 20
TETO_MUDANCAS = 12

# Estimativa grosseira e declarada como tal: ~4 caracteres por token é a regra
# de bolso para português e inglês. Serve para dizer a ordem de grandeza na
# tela, não para faturar nada.
CHARS_POR_TOKEN = 4


def tamanho_do_contexto(painel: dict[str, Any]) -> dict[str, Any]:
    """Quanto texto a análise vai mandar — respondido ANTES de mandar.

    "Se for muito, vai ser chato de API." A pergunta é justa e não tinha
    resposta na tela: quem clica em Analisar não fazia ideia se aquilo custa
    um décimo de centavo ou dez. Agora faz, antes de clicar.
    """
    corpo = dossie_markdown(dossie(painel))
    return {
        "chars": len(corpo),
        "tokens_aprox": round(len(corpo) / CHARS_POR_TOKEN),
        "caps": {"flaky": TETO_FLAKY, "recorte": TETO_RECORTE,
                 "mudancas": TETO_MUDANCAS},
    }


def dossie(painel: dict[str, Any]) -> dict[str, Any]:
    """Os números que a análise viu, guardados junto dela.

    É um RECORTE do painel, não uma cópia: os 30 runs crus e os pontos de
    cada série pesariam megabytes por análise e não acrescentam nada ao
    comparativo, que é sobre agregado.
    """
    periodo = painel.get("period") or {}
    saude = painel.get("health") or {}
    achados = painel.get("findings") or {}
    return {
        "period": periodo,
        "health": saude,
        "signals": [
            {"name": s.get("name"), "unit": s.get("unit"),
             "current": s.get("current"), "average": s.get("average"),
             "previous_average": s.get("previous_average"),
             "delta_pct": s.get("delta_pct"), "goal": s.get("goal"),
             "direction": s.get("direction"), "points": len(s.get("points") or [])}
            for s in painel.get("signals") or []
        ],
        # Tetos explícitos (change 0198). O dossiê não cresce com o número de
        # execuções — é agregado —, mas cresce com o número de CENÁRIOS
        # instáveis e de repositórios. Numa suíte grande e num dia ruim, essa
        # lista sozinha passaria de tudo o mais somado, e o que a análise
        # precisa dela são os piores, não todos.
        "flaky": [
            {"scenario": f.get("scenario"), "testcase_id": f.get("testcase_id"),
             "runs": f.get("runs"), "failures": f.get("failures"),
             "flips": f.get("flips"), "newly_flaky": f.get("newly_flaky")}
            for f in sorted(painel.get("flaky") or [],
                            key=lambda f: (-int(bool(f.get("newly_flaky"))),
                                           -(f.get("flips") or 0)))[:TETO_FLAKY]
        ],
        "flaky_total": len(painel.get("flaky") or []),
        "findings": {
            "total": achados.get("total"),
            "previous_total": achados.get("previous_total"),
            "delta_pct": achados.get("delta_pct"),
            "by_impact": achados.get("by_impact") or [],
            "top_rules": (achados.get("top_rules") or [])[:8],
            "by_wcag": (achados.get("by_wcag") or [])[:8],
        },
        "distribution": painel.get("distribution") or {},
        "by_repo": (painel.get("by_repo") or [])[:TETO_RECORTE],
        "by_origin": (painel.get("by_origin") or [])[:TETO_RECORTE],
        "errors_by_origin": (painel.get("errors_by_origin") or [])[:TETO_RECORTE],
        "by_label": painel.get("by_label") or {},
        "changes": [c.get("text")
                    for c in (painel.get("changes") or [])[:TETO_MUDANCAS]],
    }


def dossie_markdown(dados: dict[str, Any]) -> str:
    """O dossiê em texto — é isto que vai ao modelo.

    Markdown e não JSON: o modelo lê tabela melhor que árvore aninhada, e o
    texto fica conferível por quem quiser auditar o que foi perguntado.
    """
    periodo = dados.get("period") or {}
    saude = dados.get("health") or {}
    linhas = [
        f"# Observabilidade — {str(periodo.get('since'))[:10]} a"
        f" {str(periodo.get('until'))[:10]} ({periodo.get('days')} dias)",
        "",
        "## Saúde",
        f"- Execuções: {saude.get('runs')} (período anterior:"
        f" {saude.get('runs_previous')})",
        f"- Taxa de sucesso: {_numero(saude.get('success_rate'))}%"
        f" (anterior: {_numero(saude.get('success_rate_previous'))}%;"
        f" meta declarada: {_numero(saude.get('goal'))}%)",
        "",
    ]

    if dados.get("changes"):
        linhas += ["## O que mudou sozinho", ""]
        linhas += [f"- {t}" for t in dados["changes"]] + [""]

    if dados.get("by_origin"):
        linhas += [
            "## Por repositório de ORIGEM (a aplicação cujo deploy disparou)",
            "",
            "| origem | execuções | falhas | taxa | vs. anterior |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
        for item in dados["by_origin"]:
            linhas.append(
                f"| {item.get('name')} | {item.get('runs')} |"
                f" {item.get('failures')} | {_numero(item.get('success_rate'))}% |"
                f" {_numero(item.get('delta_pct'))} |")
        linhas.append("")

    if dados.get("by_repo"):
        linhas += ["## Por repositório de TESTE", "",
                   "| repositório | execuções | falhas | taxa |",
                   "| --- | ---: | ---: | ---: |"]
        for item in dados["by_repo"]:
            linhas.append(
                f"| {item.get('name')} | {item.get('runs')} |"
                f" {item.get('failures')} | {_numero(item.get('success_rate'))}% |")
        linhas.append("")

    for rotulo, itens in (dados.get("by_label") or {}).items():
        if not itens:
            continue
        linhas += [f"## Por rótulo `{rotulo}`", "",
                   f"| {rotulo} | execuções | falhas | taxa |",
                   "| --- | ---: | ---: | ---: |"]
        for item in itens:
            linhas.append(
                f"| {item.get('name')} | {item.get('runs')} |"
                f" {item.get('failures')} | {_numero(item.get('success_rate'))}% |")
        linhas.append("")

    if dados.get("signals"):
        linhas += ["## Sinais", "",
                   "| sinal | atual | média | média anterior | variação |"
                   " meta | direção declarada |",
                   "| --- | ---: | ---: | ---: | --- | ---: | --- |"]
        for s in dados["signals"]:
            linhas.append(
                f"| {s.get('name')} ({s.get('unit') or '—'}) |"
                f" {_numero(s.get('current'))} | {_numero(s.get('average'))} |"
                f" {_numero(s.get('previous_average'))} |"
                f" {_numero(s.get('delta_pct'))}% | {_numero(s.get('goal'))} |"
                f" {s.get('direction') or 'NÃO DECLARADA'} |")
        linhas.append("")

    if dados.get("flaky"):
        linhas += ["## Cenários instáveis", "",
                   "| cenário | caso | execuções | falhas | viradas | novo |",
                   "| --- | --- | ---: | ---: | ---: | --- |"]
        for f in dados["flaky"]:
            linhas.append(
                f"| {f.get('scenario')} | {f.get('testcase_id') or '—'} |"
                f" {f.get('runs')} | {f.get('failures')} | {f.get('flips')} |"
                f" {'SIM' if f.get('newly_flaky') else 'não'} |")
        linhas.append("")

    achados = dados.get("findings") or {}
    if achados.get("total"):
        linhas += [
            "## Acessibilidade",
            f"- {achados['total']} elemento(s) com violação"
            f" (anterior: {achados.get('previous_total')};"
            f" variação: {_numero(achados.get('delta_pct'))}%)",
            "- Por gravidade: "
            + ", ".join(f"{f['label']} {f['value']}"
                        for f in achados.get("by_impact") or []),
            "",
            "| regra | gravidade | WCAG | elementos |",
            "| --- | --- | --- | ---: |",
        ]
        for r in achados.get("top_rules") or []:
            linhas.append(
                f"| {r.get('rule')} | {r.get('impact')} |"
                f" {r.get('wcag') or '—'} | {r.get('count')} |")
        linhas.append("")
    return "\n".join(linhas)


# -- persistência ------------------------------------------------------------


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def proximo_id(ws) -> str:
    """`ANL-YYYYMMDD-N`: ordenável, legível e único no dia."""
    hoje = datetime.now(timezone.utc).strftime("%Y%m%d")
    base = ws.root / PASTA
    usados = {p.stem for p in base.glob(f"ANL-{hoje}-*.md")} if base.exists() else set()
    n = 1
    while f"ANL-{hoje}-{n}" in usados:
        n += 1
    return f"ANL-{hoje}-{n}"


def caminho(analise_id: str) -> str:
    return f"{PASTA}/{analise_id}.md"


def gravar(ws, analise_id: str, meta: dict[str, Any], corpo: str) -> str:
    destino = ws.root / caminho(analise_id)
    destino.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(corpo, **{k: v for k, v in meta.items() if v is not None})
    destino.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return caminho(analise_id)


def ler(ws, analise_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", analise_id or ""):
        raise AnaliseError("invalid_id", "identificador inválido", 422)
    destino = ws.root / caminho(analise_id)
    if not destino.exists():
        raise AnaliseError("not_found", f"análise {analise_id} não existe", 404)
    post = frontmatter.loads(destino.read_text(encoding="utf-8"))
    return {**post.metadata, "id": analise_id, "body": post.content,
            "path": caminho(analise_id)}


def listar(ws, limite: int = 50) -> list[dict[str, Any]]:
    """O histórico, do mais novo para o mais velho.

    Lido do DISCO e não do índice: o índice é descartável e o histórico que
    justifica uma decisão técnica não pode sumir num reindex (ADR 0001).
    """
    base = ws.root / PASTA
    if not base.exists():
        return []
    saida = []
    for arquivo in sorted(base.glob("ANL-*.md"), reverse=True)[:limite]:
        try:
            post = frontmatter.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        meta = post.metadata
        dossie_ = meta.get("dossier") or {}
        saude = (dossie_.get("health") or {})
        saida.append({
            "id": arquivo.stem,
            "created_at": meta.get("created_at"),
            "days": (dossie_.get("period") or {}).get("days"),
            "provider": meta.get("provider"),
            "saude_geral": meta.get("saude_geral"),
            "sintese": meta.get("sintese"),
            "runs": saude.get("runs"),
            "success_rate": saude.get("success_rate"),
            "findings_total": (dossie_.get("findings") or {}).get("total"),
            "riscos": len(meta.get("riscos") or []),
            "path": caminho(arquivo.stem),
        })
    return saida


def corpo_da_analise(resultado: AnaliseObservabilidade) -> str:
    """O veredito em Markdown — é o corpo do documento, e o que a tela lê."""
    linhas = [f"## Síntese", "", resultado.sintese, ""]
    if resultado.observacao_por_produto:
        linhas += ["## Por produto", "", resultado.observacao_por_produto, ""]
    if resultado.acessibilidade:
        linhas += ["## Acessibilidade", "", resultado.acessibilidade, ""]
    if resultado.riscos:
        linhas += ["## Riscos", ""]
        for risco in resultado.riscos:
            linhas.append(f"- **{risco.titulo}** ({risco.gravidade})"
                          + (f" — {risco.evidencia}" if risco.evidencia else ""))
        linhas.append("")
    if resultado.acoes:
        linhas += ["## O que fazer", ""]
        for acao in resultado.acoes:
            alvo = f" [{acao.alvo}]" if acao.alvo else ""
            linhas.append(f"- {acao.acao}{alvo}"
                          + (f" — {acao.porque}" if acao.porque else ""))
        linhas.append("")
    return "\n".join(linhas)


def analisar(provider, ws, painel: dict[str, Any], provider_nome: str,
             memoria: str = "") -> dict[str, Any]:
    """Gera a análise do período e a grava no workspace."""
    dados = dossie(painel)
    texto = dossie_markdown(dados)
    resultado = provider.complete(
        _SISTEMA, (memoria + texto) if memoria else texto,
        AnaliseObservabilidade)
    assert isinstance(resultado, AnaliseObservabilidade)
    analise_id = proximo_id(ws)
    meta = {
        "id": analise_id,
        "kind": "ci_analysis",
        "created_at": _agora(),
        "provider": provider_nome,
        "saude_geral": resultado.saude_geral,
        "sintese": resultado.sintese,
        "riscos": [r.model_dump() for r in resultado.riscos],
        "acoes": [a.model_dump() for a in resultado.acoes],
        # O dossiê vai junto: comparar duas análises é comparar os NÚMEROS que
        # cada uma viu, não o que a IA escreveu sobre eles.
        "dossier": dados,
    }
    caminho_rel = gravar(ws, analise_id, meta, corpo_da_analise(resultado))
    return {**meta, "path": caminho_rel, "body": corpo_da_analise(resultado)}


def comparar(provider, ws, id_a: str, id_b: str) -> dict[str, Any]:
    """Compara duas análises guardadas. Sempre da mais VELHA para a mais nova.

    A ordem não é detalhe: "melhorou" depende de qual veio antes, e deixar o
    chamador decidir a direção convidaria a inverter o veredito sem querer.
    """
    if id_a == id_b:
        raise AnaliseError("same_analysis",
                           "escolha duas análises diferentes", 422)
    a, b = ler(ws, id_a), ler(ws, id_b)
    if str(a.get("created_at") or "") > str(b.get("created_at") or ""):
        a, b = b, a

    def bloco(rotulo: str, analise: dict[str, Any]) -> str:
        return (f"# Análise {rotulo}: {analise['id']}"
                f" (feita em {str(analise.get('created_at'))[:10]})\n\n"
                "## Veredito escrito na época\n\n"
                f"{analise.get('body') or ''}\n\n"
                "## Números que ela viu\n\n"
                f"{dossie_markdown(analise.get('dossier') or {})}\n")

    resultado = provider.complete(
        _SISTEMA_COMPARATIVO,
        bloco("ANTERIOR", a) + "\n---\n\n" + bloco("MAIS RECENTE", b),
        ComparativoAnalises)
    assert isinstance(resultado, ComparativoAnalises)
    return {"from": a["id"], "to": b["id"],
            "from_at": a.get("created_at"), "to_at": b.get("created_at"),
            **resultado.model_dump()}
