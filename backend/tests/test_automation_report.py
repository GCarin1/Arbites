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
