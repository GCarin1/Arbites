"""Métricas e matriz de rastreabilidade — queries puras sobre o índice.

Cada métrica devolve numerador e denominador explícitos junto com o valor:
as fórmulas (intake §11) são defensáveis em reunião e a API nunca esconde
o denominador. Nenhum estado é materializado — o índice é descartável
(ADR 0001).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

FINAL_STATUSES = ("passed", "failed", "blocked", "retest")
# pior primeiro — agregação do "último resultado" de uma story
_WORST_ORDER = ["failed", "blocked", "retest", "in_progress", "pending", "passed"]


def _cutoff(days: int | None) -> str | None:
    if not days:
        return None
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _results_where(sprint: str | None, days: int | None) -> tuple[str, list[Any]]:
    sql, params = "", []
    if sprint:
        sql += " AND e.sprint = ?"
        params.append(sprint)
    cutoff = _cutoff(days)
    if cutoff:
        sql += " AND r.executed_at >= ?"
        params.append(cutoff)
    return sql, params


def requirement_coverage(conn: sqlite3.Connection, epic: str | None = None) -> dict:
    """stories `active` com ≥1 CT `ready` ÷ stories `active`."""
    where, params = "", []
    if epic:
        where, params = " AND epic_id = ?", [epic]
    total = conn.execute(
        "SELECT COUNT(*) c FROM requirements WHERE kind='story' AND status='active'"
        + where,
        params,
    ).fetchone()["c"]
    covered = conn.execute(
        "SELECT COUNT(*) c FROM requirements s WHERE s.kind='story' AND s.status='active'"
        + where
        + " AND EXISTS (SELECT 1 FROM testcases t WHERE t.story_id = s.id"
        "   AND t.status = 'ready')",
        params,
    ).fetchone()["c"]
    return {
        "formula": "stories active com >=1 CT ready / stories active",
        "numerator": covered,
        "denominator": total,
        "value": _ratio(covered, total),
    }


def execution_coverage(
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None
) -> dict:
    """CTs distintos executados no período ÷ CTs `ready`."""
    ready = conn.execute(
        "SELECT COUNT(*) c FROM testcases WHERE status='ready'"
    ).fetchone()["c"]
    where, params = _results_where(sprint, days)
    executed = conn.execute(
        "SELECT COUNT(DISTINCT r.testcase_id) c FROM results r"
        " JOIN executions e ON e.id = r.execution_id"
        f" WHERE r.status IN {FINAL_STATUSES!r}" + where,
        params,
    ).fetchone()["c"]
    return {
        "formula": "CTs distintos executados no periodo / CTs ready",
        "numerator": executed,
        "denominator": ready,
        "value": _ratio(executed, ready),
    }


def pass_rate(
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None
) -> dict:
    """`passed` ÷ resultados finais (`passed`+`failed`)."""
    where, params = _results_where(sprint, days)
    row = conn.execute(
        "SELECT SUM(CASE WHEN r.status='passed' THEN 1 ELSE 0 END) p,"
        " SUM(CASE WHEN r.status IN ('passed','failed') THEN 1 ELSE 0 END) f"
        " FROM results r JOIN executions e ON e.id = r.execution_id WHERE 1=1" + where,
        params,
    ).fetchone()
    passed, final = row["p"] or 0, row["f"] or 0
    return {
        "formula": "passed / (passed + failed)",
        "numerator": passed,
        "denominator": final,
        "value": _ratio(passed, final),
    }


def blocked_rate(
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None
) -> dict:
    """`blocked` ÷ total de resultados."""
    where, params = _results_where(sprint, days)
    row = conn.execute(
        "SELECT SUM(CASE WHEN r.status='blocked' THEN 1 ELSE 0 END) b, COUNT(*) t"
        " FROM results r JOIN executions e ON e.id = r.execution_id WHERE 1=1" + where,
        params,
    ).fetchone()
    blocked, total = row["b"] or 0, row["t"] or 0
    return {
        "formula": "blocked / total de resultados",
        "numerator": blocked,
        "denominator": total,
        "value": _ratio(blocked, total),
    }


def rework_rate(
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None
) -> dict:
    """resultados que passaram por `retest` ÷ total de resultados."""
    where, params = _results_where(sprint, days)
    total = conn.execute(
        "SELECT COUNT(*) t FROM results r JOIN executions e ON e.id = r.execution_id"
        " WHERE 1=1" + where,
        params,
    ).fetchone()["t"]
    ev_where, ev_params = "", []
    if sprint:
        ev_where += " AND e.sprint = ?"
        ev_params.append(sprint)
    cutoff = _cutoff(days)
    if cutoff:
        ev_where += " AND v.at >= ?"
        ev_params.append(cutoff)
    reworked = conn.execute(
        "SELECT COUNT(DISTINCT v.execution_id || '/' || v.testcase_id) c"
        " FROM result_events v JOIN executions e ON e.id = v.execution_id"
        " WHERE v.status = 'retest'" + ev_where,
        ev_params,
    ).fetchone()["c"]
    return {
        "formula": "resultados que passaram por retest / total de resultados",
        "numerator": reworked,
        "denominator": total,
        "value": _ratio(reworked, total),
    }


def flaky(conn: sqlite3.Connection, window: int = 5) -> dict:
    """CTs cujo resultado alternou pass/fail nas últimas N execuções."""
    rows = conn.execute(
        "SELECT r.testcase_id, r.status, e.created_at FROM results r"
        " JOIN executions e ON e.id = r.execution_id"
        " WHERE r.status IN ('passed','failed')"
        " ORDER BY r.testcase_id, e.created_at"
    ).fetchall()
    by_ct: dict[str, list[str]] = {}
    for row in rows:
        by_ct.setdefault(row["testcase_id"], []).append(row["status"])
    flaky_cts = []
    for ct_id, sequence in by_ct.items():
        tail = sequence[-window:]
        if any(a != b for a, b in zip(tail, tail[1:])):
            flaky_cts.append({"testcase_id": ct_id, "sequence": tail})
    return {
        "formula": f"CTs com transicao pass<->fail nas ultimas {window} execucoes",
        "window": window,
        "testcases": sorted(flaky_cts, key=lambda x: x["testcase_id"]),
    }


def trend(
    conn: sqlite3.Connection, days: int = 7, sprint: str | None = None
) -> list[dict]:
    """Série diária de passed/failed/blocked (eventos de resultado)."""
    cutoff = _cutoff(days)
    where, params = " AND v.at >= ?", [cutoff]
    if sprint:
        where += " AND e.sprint = ?"
        params.append(sprint)
    rows = conn.execute(
        "SELECT substr(v.at, 1, 10) day, v.status, COUNT(*) c"
        " FROM result_events v JOIN executions e ON e.id = v.execution_id"
        " WHERE v.status IN ('passed','failed','blocked')" + where +
        " GROUP BY day, v.status",
        params,
    ).fetchall()
    by_day: dict[str, dict[str, int]] = {}
    for row in rows:
        by_day.setdefault(row["day"], {})[row["status"]] = row["c"]
    today = datetime.now(timezone.utc).date()
    series = []
    for offset in range(days - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        counts = by_day.get(day, {})
        series.append(
            {
                "day": day,
                "passed": counts.get("passed", 0),
                "failed": counts.get("failed", 0),
                "blocked": counts.get("blocked", 0),
            }
        )
    return series


def traceability(
    conn: sqlite3.Connection, epic: str | None = None, sprint: str | None = None
) -> dict:
    """Matriz Epic → Story | CTs | Último resultado | Execution | Evidências | Defeitos."""
    epic_where, epic_params = "", []
    if epic:
        epic_where, epic_params = " AND id = ?", [epic]
    epics = conn.execute(
        "SELECT id, title, status FROM requirements WHERE kind='epic'" + epic_where +
        " ORDER BY id",
        epic_params,
    ).fetchall()

    sprint_where, sprint_params = "", []
    if sprint:
        sprint_where, sprint_params = " AND e.sprint = ?", [sprint]

    def last_result(ct_id: str) -> dict | None:
        row = conn.execute(
            "SELECT r.status, r.execution_id, r.executed_at FROM results r"
            " JOIN executions e ON e.id = r.execution_id"
            f" WHERE r.testcase_id = ? AND r.status IN {FINAL_STATUSES!r}"
            + sprint_where +
            " ORDER BY r.executed_at DESC LIMIT 1",
            [ct_id, *sprint_params],
        ).fetchone()
        return dict(row) if row else None

    out_epics = []
    for epic_row in epics:
        stories = conn.execute(
            "SELECT id, title, status FROM requirements"
            " WHERE kind='story' AND epic_id = ? ORDER BY id",
            (epic_row["id"],),
        ).fetchall()
        out_stories = []
        for story in stories:
            cts = conn.execute(
                "SELECT id, title, status FROM testcases WHERE story_id = ? ORDER BY id",
                (story["id"],),
            ).fetchall()
            ct_rows = []
            lasts = []
            for ct in cts:
                last = last_result(ct["id"])
                if last:
                    lasts.append((ct["id"], last))
                ct_rows.append({**dict(ct), "last_result": last})
            statuses = [last["status"] for _, last in lasts]
            agg_status = next((s for s in _WORST_ORDER if s in statuses), None)
            newest = max(lasts, key=lambda x: x[1]["executed_at"] or "")[1] if lasts else None
            evidence_count = 0
            for ct_id, last in lasts:
                evidence_count += conn.execute(
                    "SELECT COUNT(*) c FROM evidences"
                    " WHERE execution_id = ? AND testcase_id = ?",
                    (last["execution_id"], ct_id),
                ).fetchone()["c"]
            defects = [
                dict(d)
                for d in conn.execute(
                    "SELECT id, title, status, severity, testcase_id, execution_id"
                    " FROM defects WHERE testcase_id IN (SELECT id FROM testcases"
                    " WHERE story_id = ?) ORDER BY id",
                    (story["id"],),
                )
            ]
            out_stories.append(
                {
                    **dict(story),
                    "ct_count": len(cts),
                    "covered": len(cts) > 0,
                    "last_status": agg_status,
                    "last_execution": newest["execution_id"] if newest else None,
                    "evidence_count": evidence_count,
                    "defects": defects,
                    "testcases": ct_rows,
                }
            )
        out_epics.append({**dict(epic_row), "stories": out_stories})
    return {"epic_filter": epic, "sprint_filter": sprint, "epics": out_epics}


def matrix_markdown(matrix: dict) -> str:
    """Renderiza a matriz em Markdown colável no Confluence."""
    lines = ["# Matriz de rastreabilidade", ""]
    if matrix.get("sprint_filter"):
        lines.append(f"Sprint: {matrix['sprint_filter']}")
        lines.append("")
    lines.append(
        "| Epic / Story | CTs | Último resultado | Execution | Evidências | Defeitos |"
    )
    lines.append("|---|---|---|---|---|---|")
    for epic in matrix["epics"]:
        lines.append(f"| **{epic['id']} {epic['title']}** | | | | | |")
        for story in epic["stories"]:
            status = story["last_status"] or (
                "sem execução" if story["covered"] else "sem cobertura"
            )
            defects = ", ".join(d["id"] for d in story["defects"]) or "—"
            lines.append(
                f"| {story['id']} {story['title']}"
                f" | {story['ct_count']}"
                f" | {status}"
                f" | {story['last_execution'] or '—'}"
                f" | {story['evidence_count']}"
                f" | {defects} |"
            )
    lines.append("")
    return "\n".join(lines)
