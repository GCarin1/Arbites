"""Memória Histórica do Projeto — linha do tempo cronológica (estilo git
log) que cruza requisitos, defeitos, lições aprendidas, decisões
arquiteturais e interações de agentes de IA. Também alimenta chamadas de IA
com um recap do que já aconteceu no projeto — a IA "lembra" de decisões e
lições passadas conforme o projeto cresce, complementando a injeção por
similaridade de texto já existente em `ai.find_relevant_lessons`.
"""

from __future__ import annotations

import sqlite3
from typing import Any

_ALL_KINDS = (
    "requirement", "testcase", "defect", "lesson", "decision", "agent", "result",
)


def timeline(
    conn: sqlite3.Connection,
    kinds: list[str] | None = None,
    limit: int = 50,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """Eventos ordenados do mais recente para o mais antigo, cruzando as
    fontes já indexadas — nada é materializado além do já existente, exceto
    `agent_events` (novo, ver `_log_agent_event` em api.py).

    Sem `kinds` explícito, o tipo `result` (transições de resultado) fica
    FORA — é verboso por natureza e afogaria a timeline; quem quiser pede
    `kinds=...,result` (a UI oferece como opt-in).

    `date_from`/`date_to` (`YYYY-MM-DD`, inclusivos) recortam os eventos pelo
    prefixo de data de `at` — uniforme para todas as fontes, aplicado ANTES
    do corte por `limit`."""
    wanted = set(kinds) if kinds else set(_ALL_KINDS) - {"result"}
    events: list[dict[str, Any]] = []

    if "requirement" in wanted:
        for r in conn.execute(
            "SELECT id, kind, title, created FROM requirements WHERE created IS NOT NULL"
        ):
            label = "Epic criado" if r["kind"] == "epic" else "Story criada"
            events.append({
                "at": r["created"], "kind": "requirement", "id": r["id"],
                "title": r["title"], "summary": label,
            })

    if "testcase" in wanted:
        for t in conn.execute(
            "SELECT id, title, created FROM testcases WHERE created IS NOT NULL"
        ):
            events.append({
                "at": t["created"], "kind": "testcase", "id": t["id"],
                "title": t["title"], "summary": "Caso de teste criado",
            })

    if "result" in wanted:
        # transições de resultado dentro de executions (result_events) —
        # "CT-X passou/falhou em EXEC-Y"; verboso por natureza, por isso a
        # UI o deixa desligado por default (opt-in)
        label = {"passed": "passou", "failed": "falhou", "blocked": "bloqueou",
                 "retest": "voltou para reteste"}
        for ev in conn.execute(
            "SELECT v.execution_id, v.testcase_id, v.status, v.at, t.title"
            " FROM result_events v LEFT JOIN testcases t ON t.id = v.testcase_id"
            " WHERE v.status IN ('passed','failed','blocked','retest')"
        ):
            verb = label.get(ev["status"], ev["status"])
            events.append({
                "at": ev["at"], "kind": "result", "id": ev["testcase_id"],
                "title": ev["title"] or ev["testcase_id"],
                "summary": f"{ev['testcase_id']} {verb} em {ev['execution_id']}",
            })

    if "defect" in wanted or "lesson" in wanted:
        for d in conn.execute(
            "SELECT id, title, severity, opened_at, root_cause, fix FROM defects"
            " WHERE opened_at IS NOT NULL"
        ):
            if "defect" in wanted:
                sev = d["severity"] or "sem severidade"
                events.append({
                    "at": d["opened_at"], "kind": "defect", "id": d["id"],
                    "title": d["title"], "summary": f"Defeito aberto ({sev})",
                })
            if "lesson" in wanted and (d["root_cause"] or "").strip():
                summary = f"Lição registrada: {d['root_cause']}"
                if d["fix"]:
                    summary += f" — correção: {d['fix']}"
                events.append({
                    "at": d["opened_at"], "kind": "lesson", "id": d["id"],
                    "title": d["title"], "summary": summary,
                })

    if "decision" in wanted:
        for dec in conn.execute(
            "SELECT id, title, status, created FROM decisions WHERE created IS NOT NULL"
        ):
            events.append({
                "at": dec["created"], "kind": "decision", "id": dec["id"],
                "title": dec["title"],
                "summary": f"Decisão registrada ({dec['status']})",
            })

    if "agent" in wanted:
        for a in conn.execute(
            "SELECT id, at, action, target_id, target_title, summary FROM agent_events"
        ):
            events.append({
                "at": a["at"], "kind": "agent", "id": a["id"],
                "title": a["target_title"] or a["target_id"] or a["action"],
                "summary": a["summary"] or a["action"],
            })

    if date_from or date_to:
        lo = date_from or ""
        hi = date_to or "9999-12-31"
        events = [e for e in events if e["at"] and lo <= e["at"][:10] <= hi]

    events.sort(key=lambda e: e["at"] or "", reverse=True)
    return events[:limit]


# fontes → (tabela, coluna de data, filtro) para descoberta de anos; espelha
# exatamente os `SELECT`s de `timeline()` (defect e lesson dividem `defects`).
def _year_sources(wanted: set[str]) -> list[tuple[str, str, str]]:
    sources: list[tuple[str, str, str]] = []
    if "requirement" in wanted:
        sources.append(("requirements", "created", "created IS NOT NULL"))
    if "testcase" in wanted:
        sources.append(("testcases", "created", "created IS NOT NULL"))
    if "defect" in wanted or "lesson" in wanted:
        sources.append(("defects", "opened_at", "opened_at IS NOT NULL"))
    if "decision" in wanted:
        sources.append(("decisions", "created", "created IS NOT NULL"))
    if "agent" in wanted:
        sources.append(("agent_events", "at", "at IS NOT NULL"))
    if "result" in wanted:
        sources.append(("result_events", "at",
                        "at IS NOT NULL AND status IN "
                        "('passed','failed','blocked','retest')"))
    return sources


def timeline_years(
    conn: sqlite3.Connection, kinds: list[str] | None = None,
) -> list[str]:
    """Anos DISTINTOS (`YYYY`) com ao menos um evento das fontes pedidas, em
    ordem decrescente — popula o seletor de ano da UI com dados reais em vez
    de um range chutado. Mesmo default de `result` que `timeline()`."""
    wanted = set(kinds) if kinds else set(_ALL_KINDS) - {"result"}
    years: set[str] = set()
    for table, col, where in _year_sources(wanted):
        for row in conn.execute(
            f"SELECT DISTINCT substr({col}, 1, 4) AS y FROM {table} WHERE {where}"
        ):
            y = row["y"]
            if y and y.isdigit():
                years.add(y)
    return sorted(years, reverse=True)


def recent_recap(conn: sqlite3.Connection, limit: int = 5) -> str:
    """Recap curto de decisões aceitas + lições recentes, para injetar no
    prompt de IA — complementa `find_relevant_lessons` (por similaridade de
    texto ao pedido atual) com o que aconteceu de mais recente no projeto,
    independente de ter relação textual com o pedido."""
    decisions = conn.execute(
        "SELECT id, title FROM decisions WHERE status = 'accepted'"
        " ORDER BY created DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    lessons = conn.execute(
        "SELECT id, title, root_cause, fix FROM defects"
        " WHERE root_cause IS NOT NULL AND root_cause != ''"
        " ORDER BY opened_at DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    if not decisions and not lessons:
        return ""

    lines = ["Histórico recente do projeto:"]
    for d in decisions:
        lines.append(f"- Decisão {d['id']}: {d['title']}")
    for lesson in lessons:
        line = f"- Lição de {lesson['id']} ({lesson['title']}): {lesson['root_cause']}"
        if lesson["fix"]:
            line += f" — correção: {lesson['fix']}"
        lines.append(line)
    return "\n".join(lines)
