"""Agente Auditor — consolida sinais de qualidade já existentes no índice.

Não é um daemon: cada rodada é um snapshot pontual (`collect_findings`),
disparado sob demanda ou lazy (ver `api.py`, rota `/audit/latest`, que roda
uma nova auditoria quando a última passou de `auto_interval_hours`). Os
achados vêm de dados que já existem — `warnings` (indexação), stories sem
CT, defeitos abertos há muito tempo e automações quebradas — nada de
heurística nova, só consolidação com prazo.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from .metrics import automation_report

_DEFAULT_DEFECT_AGING_DAYS = 14
_DEFAULT_BROKEN_AUTOMATION_DAYS = 3

_SEVERITY_ORDER = ("bad", "warn", "info")


def collect_findings(
    conn: sqlite3.Connection,
    defect_aging_days: int | None = None,
    broken_automation_days: int | None = None,
    name_pattern: str | None = None,
) -> list[dict[str, Any]]:
    """Roda todos os checks e devolve os achados, piores-primeiro."""
    aging = defect_aging_days or _DEFAULT_DEFECT_AGING_DAYS
    broken = broken_automation_days or _DEFAULT_BROKEN_AUTOMATION_DAYS

    findings: list[dict[str, Any]] = []
    findings += _indexing_warnings(conn)
    findings += _uncovered_stories(conn)
    findings += _forgotten_defects(conn, aging)
    findings += _broken_automations(conn, broken, name_pattern)

    order = {s: i for i, s in enumerate(_SEVERITY_ORDER)}
    findings.sort(key=lambda f: order.get(f["severity"], 99))
    return findings


def _indexing_warnings(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT code, source_path, message FROM warnings ORDER BY code, source_path"
    ).fetchall()
    return [
        {
            "category": "indexing",
            "code": r["code"],
            "severity": "warn",
            "message": r["message"],
            "ref": r["source_path"],
        }
        for r in rows
    ]


def _uncovered_stories(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, title FROM requirements WHERE kind='story' AND id NOT IN"
        " (SELECT DISTINCT story_id FROM testcases WHERE story_id IS NOT NULL)"
        " ORDER BY id"
    ).fetchall()
    return [
        {
            "category": "coverage",
            "code": "uncovered_story",
            "severity": "warn",
            "message": f'{r["id"]} "{r["title"]}" sem nenhum caso de teste vinculado',
            "ref": r["id"],
        }
        for r in rows
    ]


def _forgotten_defects(conn: sqlite3.Connection, aging_days: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, title, opened_at, root_cause FROM defects WHERE status = 'open'"
    ).fetchall()
    today = date.today()
    out = []
    for r in rows:
        if not r["opened_at"]:
            continue
        try:
            age = (today - datetime.fromisoformat(r["opened_at"][:10]).date()).days
        except ValueError:
            continue
        if age < aging_days:
            continue
        has_lesson = bool((r["root_cause"] or "").strip())
        suffix = "" if has_lesson else " sem causa raiz registrada"
        out.append(
            {
                "category": "defects",
                "code": "forgotten_defect" if not has_lesson else "aging_defect",
                "severity": "bad" if age >= aging_days * 2 else "warn",
                "message": f'{r["id"]} "{r["title"]}" aberto há {age}d{suffix}',
                "ref": r["id"],
            }
        )
    return out


def _broken_automations(
    conn: sqlite3.Connection, broken_days: int, name_pattern: str | None = None,
) -> list[dict[str, Any]]:
    # mesmo padrão de nome do endpoint /metrics/automation — sem repassá-lo,
    # um padrão customizado deixaria os runs "unparsed" e o check nunca acharia
    # automação quebrada
    report = automation_report(conn, name_pattern)
    now = datetime.now(timezone.utc)
    out = []
    for repo in report["by_repo"]:
        since = repo.get("broken_since")
        if not since:
            continue
        try:
            since_dt = datetime.fromisoformat(since)
            days = (now - since_dt).days
        except (ValueError, TypeError):
            # created_at editado à mão sem fuso (workspace é editável
            # externamente, ADR 0001) subtrai naive de aware → TypeError
            days = None
        if days is not None and days < broken_days:
            continue
        label = f"{days}d" if days is not None else "tempo desconhecido"
        out.append(
            {
                "category": "automation",
                "code": "broken_automation",
                "severity": "bad",
                "message": f'{repo["repo"]} quebrado há {label}',
                "ref": repo["repo"],
            }
        )
    return out


def summarize(findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for f in findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
        by_category[f["category"]] = by_category.get(f["category"], 0) + 1
    return {"total": len(findings), "by_severity": by_severity, "by_category": by_category}


_CATEGORY_LABEL = {
    "indexing": "Indexação",
    "coverage": "Cobertura",
    "defects": "Defeitos",
    "automation": "Automação",
}


def audit_markdown(findings: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    """Renderiza o relatório em Markdown — corpo do doc persistido em audits/."""
    lines = [f"Total: {summary['total']} achado(s)", ""]
    if not findings:
        lines.append("Nenhum achado nesta rodada.")
        return "\n".join(lines)
    by_category: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        by_category.setdefault(f["category"], []).append(f)
    for category, items in by_category.items():
        lines.append(f"## {_CATEGORY_LABEL.get(category, category)}")
        for f in items:
            lines.append(f'- **[{f["severity"]}]** {f["message"]} (`{f["code"]}`)')
        lines.append("")
    return "\n".join(lines)
