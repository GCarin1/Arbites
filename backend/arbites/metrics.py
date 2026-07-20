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
    sprint: str | None, days: int | None, squad: str | None = None,
    since: str | None = None, until: str | None = None,
) -> tuple[str, list[Any]]:
    """`since`/`until` (ISO) delimitam uma janela fechada [since, until) —
    usado pela comparação período-a-período. Sem eles, `days` mantém o
    comportamento antigo (>= agora-days, aberto até agora)."""
    sql, params = "", []
    if sprint:
        sql += " AND e.sprint = ?"
        params.append(sprint)
    lower = since or _cutoff(days)
    if lower:
        sql += " AND r.executed_at >= ?"
        params.append(lower)
    if until:
        sql += " AND r.executed_at < ?"
        params.append(until)
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
            # cobertura de critérios EARS (0092): total × cobertos (critério
            # com ≥1 CT vinculado via `criteria`)
            criteria_total = conn.execute(
                "SELECT COUNT(*) c FROM criteria WHERE story_id = ?",
                (story["id"],),
            ).fetchone()["c"]
            criteria_covered = conn.execute(
                "SELECT COUNT(DISTINCT c.ears_id) c FROM criteria c"
                " WHERE c.story_id = ? AND EXISTS ("
                "  SELECT 1 FROM tc_criteria x JOIN testcases t ON t.id = x.testcase_id"
                "  WHERE x.ears_id = c.ears_id AND t.story_id = c.story_id)",
                (story["id"],),
            ).fetchone()["c"]
            out_stories.append(
                {
                    **dict(story),
                    "ct_count": len(cts),
                    "covered": len(cts) > 0,
                    "criteria_total": criteria_total,
                    "criteria_covered": criteria_covered,
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


def _mttr_and_broken(runs: list[dict]) -> tuple[float | None, str | None]:
    """MTTR (horas) e desde-quando-quebrado de uma sequência de runs (asc).

    "Verde" = `passed`; qualquer outro desfecho mantém o repo vermelho. Um
    incidente começa no 1º run não-verde após um verde (ou no início) e fecha
    no próximo verde; MTTR = média das durações fechadas. Se a série termina
    vermelha, `broken_since` = início do incidente aberto.
    """
    durations: list[float] = []
    fail_start: str | None = None
    for run in runs:
        green = run["outcome"] == "passed"
        if not green and fail_start is None:
            fail_start = run["at"]
        elif green and fail_start is not None:
            try:
                delta = datetime.fromisoformat(run["at"]) - datetime.fromisoformat(fail_start)
                durations.append(delta.total_seconds())
            except (ValueError, TypeError):
                pass
            fail_start = None
    mttr_hours = round(sum(durations) / len(durations) / 3600, 2) if durations else None
    return mttr_hours, fail_start


def automation_report(
    conn: sqlite3.Connection,
    name_pattern: str | None = None,
    days: int | None = None,
    env: str | None = None,
) -> dict:
    """Monitoramento das execuções de automação agrupado por REPOSITÓRIO.

    Cada execução não-manual (github_actions/local_run) é um run; o repo/env
    saem do `name` pelo `name_pattern` (regex com grupos nomeados). Agrega por
    repo com pior-primeiro (mais falhas), com sparkline dos runs recentes,
    MTTR (tempo até voltar ao verde) e nº de CTs flaky por repo; e no topo
    lista os CTs que mais falham e os flaky. `env` (opcional) filtra por
    ambiente. Runs cujo nome não casa o padrão contam em `unparsed`.
    """
    raw_pattern = name_pattern or DEFAULT_CI_NAME_PATTERN
    pattern_error = None
    try:
        pattern = re.compile(raw_pattern)
    except re.error as exc:
        pattern_error = str(exc)
        pattern = re.compile(DEFAULT_CI_NAME_PATTERN)

    def parse(name: str | None) -> tuple[str, str | None] | None:
        m = pattern.match(name or "")
        if not m or "repo" not in m.groupdict() or not m.group("repo"):
            return None
        return m.group("repo"), m.groupdict().get("env")

    cutoff = _cutoff(days)
    where = " WHERE e.origin != 'manual'"
    params: list[Any] = []
    if cutoff:
        where += " AND e.created_at >= ?"
        params.append(cutoff)

    # --- Query A: por RUN (desfecho, ranking por repo, sparkline, MTTR) ------
    run_sql = (
        "SELECT e.id, e.name, e.created_at,"
        " SUM(CASE WHEN r.status='passed' THEN 1 ELSE 0 END) passed,"
        " SUM(CASE WHEN r.status='failed' THEN 1 ELSE 0 END) failed,"
        " SUM(CASE WHEN r.status='blocked' THEN 1 ELSE 0 END) blocked,"
        " COUNT(r.testcase_id) total"
        " FROM executions e LEFT JOIN results r ON r.execution_id = e.id"
        + where + " GROUP BY e.id ORDER BY e.created_at ASC"  # asc → último = last
    )
    repos: dict[str, dict] = {}
    env_agg: dict[str, dict] = {}
    all_envs: set[str] = set()
    total_runs = passed_runs = failed_runs = unparsed = 0
    for row in conn.execute(run_sql, params):
        parsed = parse(row["name"])
        if parsed is None:
            unparsed += 1
            continue
        repo, run_env = parsed
        if run_env:
            all_envs.add(run_env)
        if env and run_env != env:  # filtro de ambiente
            continue
        outcome = _run_outcome(
            row["passed"] or 0, row["failed"] or 0, row["blocked"] or 0, row["total"] or 0
        )
        total_runs += 1
        passed_runs += outcome == "passed"
        failed_runs += outcome == "failed"

        agg = repos.setdefault(
            repo,
            {"repo": repo, "runs": 0, "passed": 0, "failed": 0, "other": 0,
             "envs": set(), "series": []},
        )
        agg["runs"] += 1
        agg["passed"] += outcome == "passed"
        agg["failed"] += outcome == "failed"
        agg["other"] += outcome not in ("passed", "failed")
        if run_env:
            agg["envs"].add(run_env)
        agg["series"].append({"at": row["created_at"], "outcome": outcome})

        if run_env:
            ea = env_agg.setdefault(run_env, {"env": run_env, "runs": 0, "failed": 0})
            ea["runs"] += 1
            ea["failed"] += outcome == "failed"

    # --- Query B: por RESULTADO (CTs que mais falham + flaky por repo) -------
    res_sql = (
        "SELECT e.name, r.testcase_id, r.status, t.title"
        " FROM results r JOIN executions e ON e.id = r.execution_id"
        " LEFT JOIN testcases t ON t.id = r.testcase_id" + where
    )
    ct_stats: dict[str, dict] = {}
    repo_ct_status: dict[str, dict[str, set]] = {}  # repo -> ct -> {statuses}
    for row in conn.execute(res_sql, params):
        parsed = parse(row["name"])
        if parsed is None:
            continue
        repo, run_env = parsed
        if env and run_env != env:
            continue
        ct = row["testcase_id"]
        status = row["status"]
        cs = ct_stats.setdefault(
            ct, {"testcase_id": ct, "title": row["title"], "failed": 0, "final": 0, "repos": set()}
        )
        cs["repos"].add(repo)
        if status in ("passed", "failed"):
            cs["final"] += 1
            cs["failed"] += status == "failed"
        repo_ct_status.setdefault(repo, {}).setdefault(ct, set()).add(status)

    # flaky por repo = CTs que passaram E falharam dentro dos runs daquele repo
    repo_flaky: dict[str, int] = {}
    flaky_ct: dict[str, set] = {}  # ct -> repos onde é flaky
    for repo, cts in repo_ct_status.items():
        for ct, statuses in cts.items():
            if "passed" in statuses and "failed" in statuses:
                repo_flaky[repo] = repo_flaky.get(repo, 0) + 1
                flaky_ct.setdefault(ct, set()).add(repo)

    by_repo = []
    for a in repos.values():
        mttr, broken_since = _mttr_and_broken(a["series"])
        by_repo.append(
            {
                "repo": a["repo"],
                "runs": a["runs"],
                "passed": a["passed"],
                "failed": a["failed"],
                "other": a["other"],
                "pass_rate": _ratio(a["passed"], a["passed"] + a["failed"]),
                "failure_rate": _ratio(a["failed"], a["runs"]),
                "envs": sorted(a["envs"]),
                "last_run_at": a["series"][-1]["at"] if a["series"] else None,
                "last_outcome": a["series"][-1]["outcome"] if a["series"] else None,
                "recent": a["series"][-12:],  # sparkline dos últimos runs
                "mttr_hours": mttr,
                "broken_since": broken_since,
                "flaky": repo_flaky.get(a["repo"], 0),
            }
        )
    by_repo.sort(key=lambda x: (x["failed"], x["failure_rate"] or 0, x["runs"]), reverse=True)

    top_failing = sorted(
        (
            {
                "testcase_id": c["testcase_id"],
                "title": c["title"],
                "failed": c["failed"],
                "runs": c["final"],
                "failure_rate": _ratio(c["failed"], c["final"]),
                "repos": sorted(c["repos"]),
            }
            for c in ct_stats.values()
            if c["failed"] > 0
        ),
        key=lambda x: (x["failed"], x["failure_rate"] or 0),
        reverse=True,
    )[:10]

    flaky_testcases = sorted(
        (
            {
                "testcase_id": ct,
                "title": ct_stats.get(ct, {}).get("title"),
                "repos": sorted(reps),
            }
            for ct, reps in flaky_ct.items()
        ),
        key=lambda x: x["testcase_id"],
    )

    by_env = sorted(
        (
            {"env": e["env"], "runs": e["runs"], "failed": e["failed"],
             "failure_rate": _ratio(e["failed"], e["runs"])}
            for e in env_agg.values()
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
        "envs": sorted(all_envs),
        "env_filter": env,
        "top_failing_testcases": top_failing,
        "flaky_testcases": flaky_testcases,
        "unparsed": unparsed,
        "pattern": raw_pattern,
        "pattern_error": pattern_error,
    }


def _local_date(iso_str: str | None) -> str | None:
    """Data LOCAL (`YYYY-MM-DD`) de um timestamp ISO possivelmente UTC.

    `result_events.at`/`executions.created_at` são carimbados em UTC
    (`_now()` de executions.py); campos já-locais (`date.today().isoformat()`,
    sem hora nem fuso) passam por aqui inalterados, já que
    `datetime.fromisoformat` num valor sem `T`/fuso não tem `tzinfo` para
    converter.
    """
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str)
    except ValueError:
        return iso_str[:10] or None
    if dt.tzinfo is not None:
        dt = dt.astimezone()  # fuso local do processo
    return dt.date().isoformat()


def _activity_years(conn: sqlite3.Connection) -> list[int]:
    """Anos com atividade — os dois campos UTC (`at`/`created_at`) passam por
    `_local_date` antes de extrair o ano (mesmo motivo do `activity_heatmap`:
    virada de ano UTC não coincide com virada de ano local)."""
    years: set[int] = set()

    def add(iso_str: str | None) -> None:
        local = _local_date(iso_str)
        if local:
            years.add(int(local[:4]))

    for row in conn.execute("SELECT at FROM result_events WHERE at IS NOT NULL"):
        add(row["at"])
    for row in conn.execute("SELECT created_at FROM executions WHERE created_at IS NOT NULL"):
        add(row["created_at"])
    for row in conn.execute("SELECT opened_at FROM defects WHERE opened_at IS NOT NULL"):
        add(row["opened_at"])
    for row in conn.execute("SELECT created FROM testcases WHERE created IS NOT NULL"):
        add(row["created"])
    for row in conn.execute("SELECT created FROM requirements WHERE created IS NOT NULL"):
        add(row["created"])
    return sorted(years)


def activity_heatmap(
    conn: sqlite3.Connection, days: int = 371, year: int | None = None
) -> dict:
    """Heatmap estilo GitHub da atividade de QA por dia.

    Cada dia agrega vários sinais datados do índice: casos executados
    (transições de resultado), bugs abertos, CTs/requisitos criados e runs de
    automação. Janela: `year` (ano civil) ou os últimos `days` dias; sempre
    começa alinhada à SEGUNDA (grade Seg→Dom × semanas). Devolve só os dias COM
    atividade (o frontend preenche os zeros) + os anos que têm atividade (p/ o
    seletor de ano).
    """
    today = date.today()
    if year:
        start = date(year, 1, 1)
        end = min(date(year, 12, 31), today)
    else:
        end = today
        start = end - timedelta(days=max(days, 1) - 1)
    start = start - timedelta(days=start.weekday())  # alinha à segunda-feira
    from_str, to_str = start.isoformat(), end.isoformat()

    per_day: dict[str, dict[str, int]] = {}

    def bump(day: str | None, key: str, n: int) -> None:
        if not day or not (from_str <= day <= to_str):
            return
        slot = per_day.setdefault(
            day,
            {"executions": 0, "defects": 0, "testcases": 0,
             "requirements": 0, "auto_runs": 0},
        )
        slot[key] += n

    # `result_events.at` e `executions.created_at` são carimbados em UTC
    # (_now() de executions.py); `defects.opened_at` e `testcases/
    # requirements.created` são carimbados com `date.today()` LOCAL. Bucketar
    # os dois sem converter faz atividade de fim de tarde (fusos atrás de UTC,
    # ex. Brasil) cair no dia UTC seguinte — que costuma ficar FORA da janela
    # "até hoje local" e some do heatmap. Por isso as duas fontes UTC passam
    # por `_local_date` linha a linha antes de bucketar; as três já-locais
    # seguem agregadas direto no SQL (não têm componente de hora/fuso).
    for row in conn.execute("SELECT at FROM result_events"):
        bump(_local_date(row["at"]), "executions", 1)
    for row in conn.execute("SELECT created_at FROM executions WHERE origin != 'manual'"):
        bump(_local_date(row["created_at"]), "auto_runs", 1)
    for row in conn.execute(
        "SELECT opened_at d, COUNT(*) n FROM defects WHERE opened_at IS NOT NULL GROUP BY d"
    ):
        bump(row["d"], "defects", row["n"])
    for row in conn.execute(
        "SELECT created d, COUNT(*) n FROM testcases WHERE created IS NOT NULL GROUP BY d"
    ):
        bump(row["d"], "testcases", row["n"])
    for row in conn.execute(
        "SELECT created d, COUNT(*) n FROM requirements WHERE created IS NOT NULL GROUP BY d"
    ):
        bump(row["d"], "requirements", row["n"])

    days_list = []
    totals = {"executions": 0, "defects": 0, "testcases": 0,
              "requirements": 0, "auto_runs": 0, "total": 0}
    for day, counts in sorted(per_day.items()):
        total = sum(counts.values())
        days_list.append({"date": day, **counts, "total": total})
        for k, v in counts.items():
            totals[k] += v
        totals["total"] += total

    return {
        "from": from_str,
        "to": to_str,
        "days": days_list,
        "totals": totals,
        "years": _activity_years(conn),  # anos com atividade (p/ o seletor)
        "year_filter": year,
    }


def period_pass_rate(
    conn: sqlite3.Connection, days: int = 30, sprint: str | None = None,
    squad: str | None = None,
) -> dict:
    """Pass rate da janela atual vs a janela anterior de mesmo tamanho —
    responde "melhorou ou piorou?" (Dashboard executivo). `delta` = atual −
    anterior (None se faltar dado num dos lados)."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).isoformat()
    prev_start = (now - timedelta(days=2 * days)).isoformat()

    def rate(since: str, until: str | None) -> float | None:
        where, params = _results_where(sprint, None, squad, since=since, until=until)
        row = conn.execute(
            "SELECT SUM(CASE WHEN r.status='passed' THEN 1 ELSE 0 END) p,"
            " SUM(CASE WHEN r.status IN ('passed','failed') THEN 1 ELSE 0 END) f"
            " FROM results r JOIN executions e ON e.id = r.execution_id WHERE 1=1" + where,
            params,
        ).fetchone()
        return _ratio(row["p"] or 0, row["f"] or 0)

    current = rate(start, None)
    previous = rate(prev_start, start)
    delta = round(current - previous, 4) if current is not None and previous is not None else None
    return {"days": days, "current": current, "previous": previous, "delta": delta}


def top_problems(
    conn: sqlite3.Connection, name_pattern: str | None = None, days: int | None = None,
    limit: int = 5,
) -> dict:
    """Consolida num só lugar os piores sinais que os reports já produzem:
    repositórios de automação piores, CTs que mais falham e defeitos abertos
    mais antigos. Nada de coleta nova — só agrega o que existe."""
    arep = automation_report(conn, name_pattern, days)
    worst_repos = [
        {"repo": r["repo"], "failed": r["failed"], "runs": r["runs"],
         "failure_rate": r["failure_rate"], "broken_since": r["broken_since"]}
        for r in arep["by_repo"] if r["failed"] > 0
    ][:limit]
    top_failing = arep["top_failing_testcases"][:limit]

    drep = defects_report(conn)
    oldest = sorted(
        (d for d in drep["items"] if d.get("age_days") is not None),
        key=lambda d: d["age_days"], reverse=True,
    )[:limit]
    oldest_defects = [
        {"id": d["id"], "title": d["title"], "severity": d["severity"],
         "age_days": d["age_days"]}
        for d in oldest
    ]
    return {
        "worst_repos": worst_repos,
        "top_failing_testcases": top_failing,
        "oldest_defects": oldest_defects,
    }


_HEALTH_DEFAULT_WEIGHTS = {
    "coverage": 0.30,
    "defects": 0.25,
    "automation": 0.25,
    "debt": 0.20,
}
_DEFECT_SEVERITY_PENALTY = {"critical": 25, "high": 12, "medium": 5, "low": 2, "unspecified": 5}


def health_score(
    conn: sqlite3.Connection,
    weights: dict[str, float] | None = None,
    sprint: str | None = None,
    days: int | None = None,
    squad: str | None = None,
    name_pattern: str | None = None,
) -> dict:
    """Nota única 0-100 sobre a saúde de QA — defensável em reunião: cada

    componente cita sua fórmula e contribuição, nada fica escondido atrás do
    número. Pesos configuráveis em `arbites.yaml` (`health_score.weights`);
    os 4 abaixo são o default e são renormalizados para somar 1.0 mesmo que
    o usuário informe pesos que não somem exatamente 1. Um componente sem
    dado disponível (`value: None`) não participa do score — o peso dos
    demais é renormalizado, em vez de tratar "sem dado" como "zero".
    """
    w = dict(_HEALTH_DEFAULT_WEIGHTS)
    if weights:
        w.update({k: float(v) for k, v in weights.items() if k in w})
    total_w = sum(w.values()) or 1.0
    w = {k: v / total_w for k, v in w.items()}

    req_cov = requirement_coverage(conn, None, squad)
    exec_cov = execution_coverage(conn, sprint, days, squad)
    cov_values = [v["value"] for v in (req_cov, exec_cov) if v["value"] is not None]
    coverage_pct = round(sum(cov_values) / len(cov_values) * 100) if cov_values else None

    drep = defects_report(conn, squad)
    penalty = sum(
        _DEFECT_SEVERITY_PENALTY.get(sev, 5) * n for sev, n in drep["by_severity"].items()
    )
    # 0 defeitos com "0 penalidade" é indistinguível de "nada foi criado ainda"
    # — só pontua "defects" se já existe algum CT ou defeito no workspace,
    # senão um workspace vazio ganharia 100/100 (falso positivo de saúde).
    has_qa_activity = conn.execute(
        "SELECT EXISTS(SELECT 1 FROM testcases) OR EXISTS(SELECT 1 FROM defects)"
    ).fetchone()[0]
    defects_pct = max(0, 100 - penalty) if has_qa_activity else None

    # mesmo padrão de nome do endpoint /metrics/automation — sem repassá-lo,
    # um padrão customizado deixaria todos os runs "unparsed" e o componente
    # de automação viraria None silenciosamente
    arep = automation_report(conn, name_pattern, days)
    automation_pct = round(arep["pass_rate"] * 100) if arep["pass_rate"] is not None else None

    br = blocked_rate(conn, sprint, days, squad)
    rr = rework_rate(conn, sprint, days, squad)
    fl = flaky(conn, 5, squad)
    ct_sql, ct_params = "SELECT COUNT(*) c FROM testcases WHERE 1=1", []
    if squad:
        ct_sql += " AND squad_effective = ?"
        ct_params.append(squad)
    total_ct = conn.execute(ct_sql, ct_params).fetchone()["c"]
    flaky_ratio = _ratio(len(fl["testcases"]), total_ct) if total_ct else None
    debt_inputs = [v for v in (br["value"], rr["value"], flaky_ratio) if v is not None]
    debt_pct = round(100 - (sum(debt_inputs) / len(debt_inputs) * 100)) if debt_inputs else None

    components = {
        "coverage": {
            "value": coverage_pct, "weight": round(w["coverage"], 4),
            "formula": "média(cobertura de requisito, cobertura de execução)",
        },
        "defects": {
            "value": defects_pct, "weight": round(w["defects"], 4),
            "formula": "100 - penalidade por severidade dos defeitos abertos"
                       " (critical=25, high=12, medium=5, low=2)",
        },
        "automation": {
            "value": automation_pct, "weight": round(w["automation"], 4),
            "formula": "pass rate dos runs de automação (github_actions/local_run)",
        },
        "debt": {
            "value": debt_pct, "weight": round(w["debt"], 4),
            "formula": "100 - média(taxa de bloqueio, retrabalho, proporção de CTs flaky)",
        },
    }

    available = {k: c for k, c in components.items() if c["value"] is not None}
    if not available:
        score = None
    else:
        aw = sum(c["weight"] for c in available.values()) or 1.0
        score = round(sum(c["value"] * (c["weight"] / aw) for c in available.values()))

    return {"score": score, "components": components}


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
