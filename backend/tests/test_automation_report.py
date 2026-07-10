"""Monitoramento de automação por repositório (dashboard) — origin != manual,
repo/env extraídos do nome da execução por regex configurável.
"""

from arbites import executions as exec_ops


def _ci_run(client, name, results, origin="github_actions"):
    """Cria uma execução de automação com resultados conhecidos e reindexa."""
    ws = client.ws
    tcs = [{"id": ct, "steps": []} for ct in results]
    execution = exec_ops.create(ws, name, "ci", None, None, tcs, origin=origin)
    for ct, status in results.items():
        exec_ops.set_result_status(execution, ct, status, "ci")
    exec_ops.save(ws, execution)
    client.post("/api/v1/workspace/reindex")  # sincroniza o índice do app
    return execution


def test_automation_report_groups_by_repo_worst_first(client):
    # dois runs do repo "core" (1 falhou), um run do repo "home" (passou)
    _ci_run(client, "Regression . acme/web-core.cer", {"CT-1": "passed", "CT-2": "passed"})
    _ci_run(client, "Regression . acme/web-core.cer", {"CT-1": "failed", "CT-2": "passed"})
    _ci_run(client, "Regression . acme/web-home.cer", {"CT-3": "passed"})

    report = client.get("/api/v1/metrics/automation").json()
    assert report["total_runs"] == 3
    assert report["passed_runs"] == 2
    assert report["failed_runs"] == 1
    assert report["pass_rate"] == round(2 / 3, 4)

    # pior primeiro: "core" (1 falha) antes de "home" (0 falhas)
    repos = report["by_repo"]
    assert [r["repo"] for r in repos] == ["acme/web-core", "acme/web-home"]
    core = repos[0]
    assert core["runs"] == 2 and core["failed"] == 1 and core["passed"] == 1
    assert core["failure_rate"] == 0.5
    assert core["envs"] == ["cer"]
    assert core["last_outcome"] == "failed"  # o run mais recente do core falhou

    home = repos[1]
    assert home["failed"] == 0 and home["last_outcome"] == "passed"


def test_automation_report_ignores_manual_and_unparsed(client):
    # execução manual (via API) — origin=manual, não entra no monitoramento
    ct = client.post(
        "/api/v1/testcases",
        json={"title": "Manual", "body": "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"},
    ).json()
    client.post("/api/v1/executions", json={"name": "Regression . acme/web.cer", "testcase_ids": [ct["id"]]})
    # automação com nome fora do padrão → conta como unparsed, não ranqueia
    _ci_run(client, "run avulso sem padrao", {"CT-9": "failed"}, origin="local_run")

    report = client.get("/api/v1/metrics/automation").json()
    assert report["total_runs"] == 0  # o manual é ignorado; o local_run não parseia
    assert report["unparsed"] == 1
    assert report["by_repo"] == []


def test_automation_report_custom_pattern_from_config(client):
    import yaml

    cfg = client.ws.config()
    # padrão do usuário: "<repo>#<env>" (sem nome, sem ponto)
    cfg["ci_monitoring"] = {"name_pattern": r"^(?P<repo>[^#]+)#(?P<env>\w+)$"}
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    _ci_run(client, "team/api#staging", {"CT-1": "failed"})
    report = client.get("/api/v1/metrics/automation").json()
    assert report["by_repo"][0]["repo"] == "team/api"
    assert report["by_repo"][0]["envs"] == ["staging"]


def test_automation_report_invalid_pattern_reports_error(client):
    import yaml

    cfg = client.ws.config()
    cfg["ci_monitoring"] = {"name_pattern": r"(?P<repo>["}  # regex quebrada
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    report = client.get("/api/v1/metrics/automation").json()
    assert report["pattern_error"] is not None  # não derruba a rota; sinaliza o erro


def test_automation_report_empty_when_no_runs(client):
    report = client.get("/api/v1/metrics/automation").json()
    assert report["total_runs"] == 0 and report["by_repo"] == [] and report["unparsed"] == 0


def test_top_failing_testcases_ranked(client):
    _ci_run(client, "Reg . acme/api.cer", {"CT-1": "failed", "CT-2": "passed"})
    _ci_run(client, "Reg . acme/api.cer", {"CT-1": "failed", "CT-2": "failed"})
    _ci_run(client, "Reg . acme/web.cer", {"CT-1": "failed"})

    report = client.get("/api/v1/metrics/automation").json()
    top = report["top_failing_testcases"]
    # CT-1 falhou 3x (em 2 repos), CT-2 1x
    assert top[0]["testcase_id"] == "CT-1"
    assert top[0]["failed"] == 3
    assert sorted(top[0]["repos"]) == ["acme/api", "acme/web"]
    assert top[1]["testcase_id"] == "CT-2" and top[1]["failed"] == 1


def test_flaky_per_repo(client):
    # CT-1 alterna pass/fail no mesmo repo → flaky; CT-2 sempre passa
    _ci_run(client, "Reg . acme/api.cer", {"CT-1": "passed", "CT-2": "passed"})
    _ci_run(client, "Reg . acme/api.cer", {"CT-1": "failed", "CT-2": "passed"})

    report = client.get("/api/v1/metrics/automation").json()
    api_repo = next(r for r in report["by_repo"] if r["repo"] == "acme/api")
    assert api_repo["flaky"] == 1
    assert [f["testcase_id"] for f in report["flaky_testcases"]] == ["CT-1"]
    assert report["flaky_testcases"][0]["repos"] == ["acme/api"]


def test_recent_sparkline_and_mttr(client):
    from datetime import datetime, timedelta, timezone

    from arbites import executions as exec_ops

    ws = client.ws
    base = datetime(2026, 6, 1, tzinfo=timezone.utc)

    def run_at(name, results, when):
        tcs = [{"id": ct, "steps": []} for ct in results]
        ex = exec_ops.create(ws, name, "ci", None, None, tcs, origin="github_actions")
        for ct, st in results.items():
            exec_ops.set_result_status(ex, ct, st, "ci")
        ex["created_at"] = when.isoformat()  # controla o tempo p/ o MTTR
        exec_ops.save(ws, ex)

    # passou (dia 0) → falhou (dia 1) → voltou a passar (dia 3): recuperou em 2 dias
    run_at("Reg . acme/api.cer", {"CT-1": "passed"}, base)
    run_at("Reg . acme/api.cer", {"CT-1": "failed"}, base + timedelta(days=1))
    run_at("Reg . acme/api.cer", {"CT-1": "passed"}, base + timedelta(days=3))
    client.post("/api/v1/workspace/reindex")

    report = client.get("/api/v1/metrics/automation").json()
    row = report["by_repo"][0]
    assert [c["outcome"] for c in row["recent"]] == ["passed", "failed", "passed"]
    assert row["mttr_hours"] == 48.0  # 2 dias
    assert row["broken_since"] is None  # terminou verde


def test_env_filter(client):
    _ci_run(client, "Reg . acme/api.cer", {"CT-1": "failed"})  # env=cer
    _ci_run(client, "Reg . acme/api.prod", {"CT-2": "passed"})  # env=prod

    full = client.get("/api/v1/metrics/automation").json()
    assert set(full["envs"]) == {"cer", "prod"}
    assert full["total_runs"] == 2

    cer = client.get("/api/v1/metrics/automation", params={"env": "cer"}).json()
    assert cer["total_runs"] == 1 and cer["failed_runs"] == 1
    assert cer["by_repo"][0]["envs"] == ["cer"]
    # o dropdown de ambiente segue listando todos, mesmo filtrado
    assert set(cer["envs"]) == {"cer", "prod"}
