"""Métricas e matriz de rastreabilidade — queries puras sobre o índice.

Cada métrica devolve numerador e denominador explícitos junto com o valor:
as fórmulas (intake §11) são defensáveis em reunião e a API nunca esconde
o denominador. Nenhum estado é materializado — o índice é descartável
(ADR 0001).
"""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Any

FINAL_STATUSES = ("passed", "failed", "blocked", "retest")
# pior primeiro — agregação do "último resultado" de uma story
_WORST_ORDER = ["failed", "blocked", "retest", "in_progress", "pending", "passed"]

# Padrão GENÉRICO (sem referência a empresa/projeto) que separa o nome de uma
# execução de automação em `<nome> <sep> <repo>.<ambiente>`. Ex.:
# "Regression . acme/web-core.cer" → name=Regression repo=acme/web-core env=cer.
# O usuário sobrescreve em arbites.yaml (`ci_monitoring.name_pattern`) para o
# seu próprio padrão de nomes; grupo `repo` é obrigatório, `env` é opcional.
DEFAULT_CI_NAME_PATTERN = r"^(?P<name>.+?)\s*[.\-]\s*(?P<repo>\S+)\.(?P<env>[^.\s]+)\s*$"


def _cutoff(days: int | None) -> str | None:
    if not days:
        return None
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


# métricas em que "menor é melhor" (default de direção quando não configurado)
_LOWER_IS_BETTER = {"blocked_rate", "rework_rate"}


def threshold_status(value: float | None, cfg: dict[str, Any]) -> str:
    """Semáforo de uma métrica vs sua meta: ok | warn | bad | none.

    `cfg` = {warn, bad, direction?}. `direction` "up" (maior melhor, default)
    ou "down" (menor melhor). Sem valor ou sem warn/bad → "none".
    """
    if value is None or "warn" not in cfg or "bad" not in cfg:
        return "none"
    warn, bad = float(cfg["warn"]), float(cfg["bad"])
    if cfg.get("direction", "up") == "down":
        if value <= warn:
            return "ok"
        return "warn" if value <= bad else "bad"
    if value >= warn:
        return "ok"
    return "warn" if value >= bad else "bad"


def annotate_thresholds(summary: dict, thresholds: dict[str, Any] | None) -> dict:
    """Anota cada métrica do summary com `status` e a `threshold` usada."""
    thresholds = thresholds or {}
    for key, metric in summary.items():
        if not isinstance(metric, dict) or "value" not in metric:
            continue
        cfg = dict(thresholds.get(key) or {})
        if cfg and "direction" not in cfg:
            cfg["direction"] = "down" if key in _LOWER_IS_BETTER else "up"
        metric["threshold"] = cfg or None
        metric["status"] = threshold_status(metric.get("value"), cfg)
    return summary


_SQUAD_CT = " AND {col} IN (SELECT id FROM testcases WHERE squad_effective = ?)"

# predicado do squad efetivo de uma story (própria squad → herda do epic)
_SQUAD_STORY = (
    " AND COALESCE(NULLIF(s.squad, ''),"
    " (SELECT NULLIF(e2.squad, '') FROM requirements e2 WHERE e2.id = s.epic_id)) = ?"
)


def _results_where(
    sprint: str | None, days: int | None, squad: str | None = None
) -> tuple[str, list[Any]]:
    sql, params = "", []
    if sprint:
        sql += " AND e.sprint = ?"
        params.append(sprint)
    cutoff = _cutoff(days)
    if cutoff:
        sql += " AND r.executed_at >= ?"
        params.append(cutoff)
    if squad:
        sql += _SQUAD_CT.format(col="r.testcase_id")
        params.append(squad)
    return sql, params


def requirement_coverage(
    conn: sqlite3.Connection, epic: str | None = None, squad: str | None = None
) -> dict:
    """stories `active` com ≥1 CT `ready` ÷ stories `active`."""
    # `s.` alias já usado no COALESCE do squad — total também precisa do alias
    where, params = "", []
    if epic:
        where += " AND s.epic_id = ?"
        params.append(epic)
    if squad:
        where += _SQUAD_STORY
        params.append(squad)
    total = conn.execute(
        "SELECT COUNT(*) c FROM requirements s WHERE s.kind='story' AND s.status='active'"
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
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None,
    squad: str | None = None,
) -> dict:
    """CTs distintos executados no período ÷ CTs `ready`."""
    ready_sql, ready_params = "SELECT COUNT(*) c FROM testcases WHERE status='ready'", []
    if squad:
        ready_sql += " AND squad_effective = ?"
        ready_params.append(squad)
    ready = conn.execute(ready_sql, ready_params).fetchone()["c"]
    where, params = _results_where(sprint, days, squad)
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
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None,
    squad: str | None = None,
) -> dict:
    """`passed` ÷ resultados finais (`passed`+`failed`)."""
    where, params = _results_where(sprint, days, squad)
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
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None,
    squad: str | None = None,
) -> dict:
    """`blocked` ÷ total de resultados."""
    where, params = _results_where(sprint, days, squad)
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
    conn: sqlite3.Connection, sprint: str | None = None, days: int | None = None,
    squad: str | None = None,
) -> dict:
    """resultados que passaram por `retest` ÷ total de resultados."""
    where, params = _results_where(sprint, days, squad)
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
    if squad:
        ev_where += _SQUAD_CT.format(col="v.testcase_id")
        ev_params.append(squad)
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


def flaky(conn: sqlite3.Connection, window: int = 5, squad: str | None = None) -> dict:
    """CTs cujo resultado alternou pass/fail nas últimas N execuções."""
    where, params = "", []
    if squad:
        where = _SQUAD_CT.format(col="r.testcase_id")
        params.append(squad)
    rows = conn.execute(
        "SELECT r.testcase_id, r.status, e.created_at FROM results r"
        " JOIN executions e ON e.id = r.execution_id"
        " WHERE r.status IN ('passed','failed')" + where +
        " ORDER BY r.testcase_id, e.created_at",
        params,
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
    conn: sqlite3.Connection, days: int = 7, sprint: str | None = None,
    squad: str | None = None,
) -> list[dict]:
    """Série diária de passed/failed/blocked pelo resultado líquido do dia.

    Cada par (execução, testcase) conta uma vez por dia, pelo status da
    última transição registrada naquele dia — arrastar o mesmo CT entre
    colunas não infla a contagem (a fonte `result_events` é um log de
    transições, não de resultados distintos).
    """
    cutoff = _cutoff(days)
    where, params = " AND v.at >= ?", [cutoff]
    if sprint:
        where += " AND e.sprint = ?"
        params.append(sprint)
    if squad:
        where += _SQUAD_CT.format(col="v.testcase_id")
        params.append(squad)
    rows = conn.execute(
        "SELECT day, status, COUNT(*) c FROM ("
        "  SELECT substr(v.at, 1, 10) day, v.status,"
        "    ROW_NUMBER() OVER ("
        "      PARTITION BY v.execution_id, v.testcase_id, substr(v.at, 1, 10)"
        "      ORDER BY v.at DESC, v.rowid DESC) rn"
        "  FROM result_events v JOIN executions e ON e.id = v.execution_id"
        "  WHERE 1=1" + where +
        ") WHERE rn = 1 AND status IN ('passed','failed','blocked')"
        " GROUP BY day, status",
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
    conn: sqlite3.Connection, epic: str | None = None, sprint: str | None = None,
    squad: str | None = None,
) -> dict:
    """Matriz Epic → Story | CTs | Último resultado | Execution | Evidências | Defeitos."""
    epic_where, epic_params = "", []
    if epic:
        epic_where, epic_params = " AND id = ?", [epic]
    ct_squad_where = " AND squad_effective = ?" if squad else ""
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
                "SELECT id, title, status FROM testcases WHERE story_id = ?"
                + ct_squad_where + " ORDER BY id",
                ([story["id"], squad] if squad else [story["id"]]),
            ).fetchall()
            if squad and not cts:
                continue  # squad: oculta stories sem CT no squad
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
        if squad and not out_stories:
            continue  # squad: oculta epics sem story no squad
        out_epics.append({**dict(epic_row), "stories": out_stories})
    return {"epic_filter": epic, "sprint_filter": sprint, "squad_filter": squad,
            "epics": out_epics}


_SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def defects_report(conn: sqlite3.Connection, squad: str | None = None) -> dict:
    """Painel de defeitos abertos: aging (dias em aberto), severidade e squad.

    Squad do defeito = squad efetivo do CT vinculado (LEFT JOIN). Aging usa
    `opened_at`; defeitos antigos sem data ficam com `age_days: null`.
    """
    where, params = "WHERE d.status = 'open'", []
    if squad:
        where += " AND t.squad_effective = ?"
        params.append(squad)
    rows = conn.execute(
        "SELECT d.id, d.title, d.severity, d.testcase_id, d.execution_id,"
        " d.external_key, d.opened_at, t.squad_effective squad"
        " FROM defects d LEFT JOIN testcases t ON t.id = d.testcase_id "
        + where + " ORDER BY d.opened_at ASC, d.id ASC",
        params,
    ).fetchall()

    # data local (o `opened` do defeito é carimbado com date.today() local);
    # usar UTC aqui causaria aging off-by-one à noite em fusos atrás do UTC.
    today = date.today()
    by_severity: dict[str, int] = {}
    by_squad: dict[str, int] = {}
    buckets = {"0-7": 0, "8-30": 0, "30+": 0}
    items = []
    for r in rows:
        age = None
        if r["opened_at"]:
            try:
                age = (today - datetime.fromisoformat(r["opened_at"][:10]).date()).days
            except ValueError:
                age = None
        severity = r["severity"] or "unspecified"
        squad_label = r["squad"] or "sem squad"
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_squad[squad_label] = by_squad.get(squad_label, 0) + 1
        if age is not None:
            key = "0-7" if age <= 7 else "8-30" if age <= 30 else "30+"
            buckets[key] += 1
        items.append({**dict(r), "squad": squad_label, "age_days": age})

    ordered_sev = {
        s: by_severity[s]
        for s in (*_SEVERITY_ORDER, "unspecified")
        if s in by_severity
    }
    return {
        "squad_filter": squad,
        "open_count": len(items),
        "by_severity": ordered_sev,
        "by_squad": dict(sorted(by_squad.items())),
        "aging_buckets": buckets,
        "items": items,
    }


def _run_outcome(passed: int, failed: int, blocked: int, total: int) -> str:
    """Desfecho de UMA execução de automação a partir dos seus resultados."""
    if total == 0:
        return "no_results"  # run sem resultados (workflow errou / artifact vazio)
    if failed:
        return "failed"
    if blocked:
        return "blocked"
    if passed == total:
        return "passed"
    return "partial"  # parte passou, resto pendente/in_progress


def automation_report(
    conn: sqlite3.Connection,
    name_pattern: str | None = None,
    days: int | None = None,
) -> dict:
    """Monitoramento das execuções de automação agrupado por REPOSITÓRIO.

    Cada execução não-manual (github_actions/local_run) é um run; o repo/env
    saem do `name` pelo `name_pattern` (regex com grupos nomeados). Agrega por
    repo com pior-primeiro (mais falhas) para responder "quais repos falham
    mais". Runs cujo nome não casa o padrão contam em `unparsed` (sinal de que
    o padrão precisa de ajuste) e não entram no ranking.
    """
    raw_pattern = name_pattern or DEFAULT_CI_NAME_PATTERN
    pattern_error = None
    try:
        pattern = re.compile(raw_pattern)
    except re.error as exc:
        pattern_error = str(exc)
        pattern = re.compile(DEFAULT_CI_NAME_PATTERN)

    sql = (
        "SELECT e.id, e.name, e.created_at,"
        " SUM(CASE WHEN r.status='passed' THEN 1 ELSE 0 END) passed,"
        " SUM(CASE WHEN r.status='failed' THEN 1 ELSE 0 END) failed,"
        " SUM(CASE WHEN r.status='blocked' THEN 1 ELSE 0 END) blocked,"
        " COUNT(r.testcase_id) total"
        " FROM executions e LEFT JOIN results r ON r.execution_id = e.id"
        " WHERE e.origin != 'manual'"
    )
    params: list[Any] = []
    cutoff = _cutoff(days)
    if cutoff:
        sql += " AND e.created_at >= ?"
        params.append(cutoff)
    sql += " GROUP BY e.id ORDER BY e.created_at ASC"  # asc → o último vira "last"

    repos: dict[str, dict] = {}
    envs: dict[str, dict] = {}
    total_runs = passed_runs = failed_runs = unparsed = 0
    for row in conn.execute(sql, params):
        m = pattern.match(row["name"] or "")
        if not m or "repo" not in m.groupdict() or not m.group("repo"):
            unparsed += 1
            continue
        repo = m.group("repo")
        env = m.groupdict().get("env")
        outcome = _run_outcome(
            row["passed"] or 0, row["failed"] or 0, row["blocked"] or 0, row["total"] or 0
        )
        total_runs += 1
        passed_runs += outcome == "passed"
        failed_runs += outcome == "failed"

        agg = repos.setdefault(
            repo,
            {"repo": repo, "runs": 0, "passed": 0, "failed": 0, "other": 0,
             "envs": set(), "last_run_at": None, "last_outcome": None},
        )
        agg["runs"] += 1
        agg["passed"] += outcome == "passed"
        agg["failed"] += outcome == "failed"
        agg["other"] += outcome not in ("passed", "failed")
        if env:
            agg["envs"].add(env)
        agg["last_run_at"] = row["created_at"]  # asc → última linha ganha
        agg["last_outcome"] = outcome

        if env:
            ea = envs.setdefault(env, {"env": env, "runs": 0, "failed": 0})
            ea["runs"] += 1
            ea["failed"] += outcome == "failed"

    by_repo = [
        {
            "repo": a["repo"],
            "runs": a["runs"],
            "passed": a["passed"],
            "failed": a["failed"],
            "other": a["other"],
            "pass_rate": _ratio(a["passed"], a["passed"] + a["failed"]),
            "failure_rate": _ratio(a["failed"], a["runs"]),
            "envs": sorted(a["envs"]),
            "last_run_at": a["last_run_at"],
            "last_outcome": a["last_outcome"],
        }
        for a in repos.values()
    ]
    # pior primeiro: mais falhas, depois maior taxa de falha, depois mais runs
    by_repo.sort(
        key=lambda x: (x["failed"], x["failure_rate"] or 0, x["runs"]), reverse=True
    )
    by_env = sorted(
        (
            {"env": e["env"], "runs": e["runs"], "failed": e["failed"],
             "failure_rate": _ratio(e["failed"], e["runs"])}
            for e in envs.values()
        ),
        key=lambda x: (x["failed"], x["failure_rate"] or 0),
        reverse=True,
    )
    return {
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "failed_runs": failed_runs,
        "pass_rate": _ratio(passed_runs, passed_runs + failed_runs),
        "by_repo": by_repo,
        "by_env": by_env,
        "unparsed": unparsed,
        "pattern": raw_pattern,
        "pattern_error": pattern_error,
    }


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
