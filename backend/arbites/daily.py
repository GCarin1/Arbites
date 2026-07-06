"""Daily digest (M11) — snapshot de métricas, contexto do dia e render p/ IA.

O contexto de um dia junta quatro fontes que o índice já tem: afazeres
(todos), atividade do QA (execuções e defeitos daquele dia), diff de métricas
(snapshot do dia vs. dia anterior) e defeitos abertos. A digestão por IA
(ai.generate_daily) consome o markdown de `context_markdown`. Nada aqui grava
a daily — isso é ação explícita do usuário (ver api).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from . import metrics as metrics_ops
from .workspace import Workspace

_METRIC_LABELS = {
    "requirement_coverage": "Cobertura de requisito",
    "execution_coverage": "Cobertura de execução",
    "pass_rate": "Pass rate",
    "blocked_rate": "Taxa de bloqueio",
    "rework_rate": "Retrabalho",
}


def snapshot_path(ws: Workspace, day: str) -> Path:
    return ws.root / "metrics" / f"{day}.json"


def save_snapshot(ws: Workspace, conn: sqlite3.Connection, day: str | None = None) -> dict:
    """Grava o snapshot das 5 métricas do dia em metrics/AAAA-MM-DD.json."""
    day = day or date.today().isoformat()
    summary = {
        "requirement_coverage": metrics_ops.requirement_coverage(conn),
        "execution_coverage": metrics_ops.execution_coverage(conn),
        "pass_rate": metrics_ops.pass_rate(conn),
        "blocked_rate": metrics_ops.blocked_rate(conn),
        "rework_rate": metrics_ops.rework_rate(conn),
    }
    snapshot = {"date": day, "metrics": {k: v["value"] for k, v in summary.items()}}
    path = snapshot_path(ws, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return snapshot


def load_snapshot(ws: Workspace, day: str) -> dict | None:
    path = snapshot_path(ws, day)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def metrics_diff(ws: Workspace, day: str) -> dict:
    """Diff das métricas do dia vs. dia anterior (a partir dos snapshots)."""
    prev = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    today_snap = load_snapshot(ws, day)
    prev_snap = load_snapshot(ws, prev)
    rows = []
    keys = (today_snap or {}).get("metrics", {}).keys() or _METRIC_LABELS.keys()
    for key in keys:
        cur = (today_snap or {}).get("metrics", {}).get(key)
        old = (prev_snap or {}).get("metrics", {}).get(key)
        delta = None
        if cur is not None and old is not None:
            delta = round(cur - old, 4)
        rows.append({"metric": key, "label": _METRIC_LABELS.get(key, key),
                     "today": cur, "previous": old, "delta": delta})
    return {"date": day, "previous_date": prev,
            "has_today": today_snap is not None, "has_previous": prev_snap is not None,
            "metrics": rows}


def day_activity(conn: sqlite3.Connection, day: str) -> dict:
    """Atividade do QA no dia: execuções movimentadas e defeitos abertos."""
    executions = [
        dict(r)
        for r in conn.execute(
            "SELECT v.execution_id, e.name, COUNT(*) events,"
            " SUM(CASE WHEN v.status='passed' THEN 1 ELSE 0 END) passed,"
            " SUM(CASE WHEN v.status='failed' THEN 1 ELSE 0 END) failed,"
            " SUM(CASE WHEN v.status='blocked' THEN 1 ELSE 0 END) blocked"
            " FROM result_events v JOIN executions e ON e.id = v.execution_id"
            " WHERE substr(v.at,1,10) = ? GROUP BY v.execution_id ORDER BY v.execution_id",
            (day,),
        )
    ]
    defects_opened = [
        dict(r)
        for r in conn.execute(
            "SELECT id, title, severity FROM defects WHERE opened_at = ? ORDER BY id",
            (day,),
        )
    ]
    return {"executions": executions, "defects_opened": defects_opened}


def _todos_context(conn: sqlite3.Connection) -> dict:
    def rows(where: str, params: tuple = ()) -> list[dict]:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT id, title, status, due, squad FROM todos WHERE " + where
                + " ORDER BY due IS NULL, due, id",
                params,
            )
        ]

    return {
        "blocked": rows("status = 'blocked'"),
        "in_progress": rows("status IN ('open','doing')"),
        "done_count": conn.execute(
            "SELECT COUNT(*) c FROM todos WHERE status='done'"
        ).fetchone()["c"],
    }


def build_context(ws: Workspace, conn: sqlite3.Connection, day: str) -> dict:
    """Contexto completo de um dia — insumo da daily (manual ou por IA)."""
    return {
        "date": day,
        "todos": _todos_context(conn),
        "activity": day_activity(conn, day),
        "metrics_diff": metrics_diff(ws, day),
        "defects_open": metrics_ops.defects_report(conn),
    }


def context_markdown(ctx: dict) -> str:
    """Renderiza o contexto em markdown p/ alimentar a IA (ou leitura humana)."""
    lines = [f"# Contexto da daily — {ctx['date']}", ""]

    todos = ctx["todos"]
    lines.append("## Afazeres")
    if todos["blocked"]:
        lines.append("Impedimentos (bloqueados):")
        lines += [f"- {t['id']} {t['title']}" for t in todos["blocked"]]
    lines.append("Em andamento/abertos:")
    lines += [
        f"- {t['id']} {t['title']} (prazo: {t['due'] or '—'})" for t in todos["in_progress"]
    ] or ["- (nenhum)"]
    lines.append(f"Concluídos acumulados: {todos['done_count']}")
    lines.append("")

    act = ctx["activity"]
    lines.append("## Atividade do dia")
    if act["executions"]:
        for e in act["executions"]:
            lines.append(
                f"- Execução {e['execution_id']} ({e['name']}): "
                f"{e['passed']} passed, {e['failed']} failed, {e['blocked']} blocked"
            )
    else:
        lines.append("- Sem execuções movimentadas.")
    if act["defects_opened"]:
        lines.append("Defeitos abertos hoje:")
        lines += [f"- {d['id']} [{d['severity']}] {d['title']}" for d in act["defects_opened"]]
    lines.append("")

    diff = ctx["metrics_diff"]
    lines.append(f"## Métricas (vs. {diff['previous_date']})")
    for m in diff["metrics"]:
        def pct(v: Any) -> str:
            return "—" if v is None else f"{round(v * 100)}%"
        delta = "" if m["delta"] is None else f" ({'+' if m['delta'] >= 0 else ''}{round(m['delta']*100)} p.p.)"
        lines.append(f"- {m['label']}: {pct(m['today'])} (antes {pct(m['previous'])}){delta}")
    lines.append("")

    defects = ctx["defects_open"]
    lines.append(f"## Defeitos abertos: {defects['open_count']}")
    if defects["by_severity"]:
        lines.append(
            "Por severidade: "
            + ", ".join(f"{k} {v}" for k, v in defects["by_severity"].items())
        )
    lines.append("")
    return "\n".join(lines)
