"""Leitor de resultado axe-core → achados estruturados (change 0175).

Acessibilidade não cabe num número. `violacoes_axe: 14` diz que piorou, não
diz **o quê**: qual regra, com que gravidade, contra qual critério da WCAG,
em que página. Sem isso não há como priorizar, e um painel de acessibilidade
vira um velocímetro que ninguém sabe o que fazer com.

O pipeline publica o JSON cru do axe-core como anexo `kind: "axe"` e pronto:
exigir que ele reescreva tudo no manifesto seria pedir trabalho para uma
informação que a ferramenta já entrega estruturada.
"""

from __future__ import annotations

import json
import re
from typing import Any

# `wcag143` → 1.4.3. As tags do axe carregam o critério colado; é a única
# fonte do número, e sem ele o achado não liga na norma que o time cobra.
_CRITERIO = re.compile(r"^wcag(\d)(\d)(\d+)$")
# `wcag2aa`, `wcag21aa`, `wcag22aaa` → o nível de conformidade
_NIVEL = re.compile(r"^wcag(\d)(\d)?(a{1,3})$")

IMPACTOS = ("critical", "serious", "moderate", "minor")


def _criterio_e_nivel(tags: list[str]) -> tuple[str | None, str | None]:
    criterio = nivel = None
    for tag in tags or []:
        t = str(tag).strip().lower()
        m = _CRITERIO.match(t)
        if m and criterio is None:
            criterio = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
            continue
        m = _NIVEL.match(t)
        if m and nivel is None:
            nivel = m.group(3).upper()
    return criterio, nivel


def _de_um_resultado(doc: dict[str, Any]) -> list[dict[str, Any]]:
    pagina = doc.get("url") or doc.get("testUrl") or None
    saida = []
    for violacao in doc.get("violations") or []:
        if not isinstance(violacao, dict):
            continue
        regra = str(violacao.get("id") or "").strip()
        if not regra:
            continue
        criterio, nivel = _criterio_e_nivel(violacao.get("tags") or [])
        nos = violacao.get("nodes") or []
        saida.append({
            "category": "accessibility",
            "rule": regra,
            # O axe classifica em quatro níveis; o que vier fora deles entra
            # como "unknown" em vez de sumir — some seria mentir na soma.
            "impact": (str(violacao.get("impact") or "").lower()
                       if str(violacao.get("impact") or "").lower() in IMPACTOS
                       else "unknown"),
            "wcag": criterio,
            "level": nivel,
            # Quantos ELEMENTOS violam, não quantas regras: é o tamanho do
            # trabalho, e é o número que o time usa para priorizar.
            "count": len(nos) or 1,
            "page": pagina,
            "help": violacao.get("help") or violacao.get("description"),
            "help_url": violacao.get("helpUrl"),
        })
    return saida


def ler_axe(bruto: bytes) -> list[dict[str, Any]]:
    """Achados de um JSON do axe-core.

    Aceita o resultado de uma página (objeto) e o de várias (lista), porque
    uma varredura de micro-frontends produz uma por rota e juntá-las num
    arquivo só é o caminho natural de quem escreve o workflow.
    """
    try:
        doc = json.loads(bruto.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    if isinstance(doc, dict) and "violations" not in doc:
        # alguns runners embrulham: {"results": {...}} ou {"pages": [...]}
        for chave in ("results", "pages", "runs"):
            if chave in doc:
                doc = doc[chave]
                break
    if isinstance(doc, dict):
        return _de_um_resultado(doc)
    if isinstance(doc, list):
        saida: list[dict[str, Any]] = []
        for item in doc:
            if isinstance(item, dict):
                saida.extend(_de_um_resultado(item))
        return saida
    return []


def normalizar_achados(brutos: Any) -> list[dict[str, Any]]:
    """Achados declarados direto no manifesto, para quem não usa axe.

    A forma é a mesma do leitor do axe: um painel que lê duas formas para a
    mesma coisa acaba com dois caminhos de agregação e uma divergência.
    """
    saida = []
    for bruto in brutos or []:
        if not isinstance(bruto, dict):
            continue
        regra = str(bruto.get("rule") or bruto.get("name") or "").strip()
        if not regra:
            continue
        try:
            quantos = int(bruto.get("count") or 1)
        except (TypeError, ValueError):
            quantos = 1
        impacto = str(bruto.get("impact") or "").lower()
        saida.append({
            "category": str(bruto.get("category") or "quality"),
            "rule": regra,
            "impact": impacto if impacto in IMPACTOS else "unknown",
            "wcag": bruto.get("wcag"),
            "level": bruto.get("level"),
            "count": max(quantos, 0),
            "page": bruto.get("page") or bruto.get("url"),
            "help": bruto.get("help"),
            "help_url": bruto.get("help_url") or bruto.get("helpUrl"),
        })
    return saida
