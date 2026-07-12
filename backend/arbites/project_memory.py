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

_ALL_KINDS = ("requirement", "defect", "lesson", "decision", "agent")


def timeline(
    conn: sqlite3.Connection, kinds: list[str] | None = None, limit: int = 50,
) -> list[dict[str, Any]]:
    """Eventos ordenados do mais recente para o mais antigo, cruzando as
    fontes já indexadas — nada é materializado além do já existente, exceto
    `agent_events` (novo, ver `_log_agent_event` em api.py)."""
    wanted = set(kinds) if kinds else set(_ALL_KINDS)
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

    events.sort(key=lambda e: e["at"] or "", reverse=True)
    return events[:limit]


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
