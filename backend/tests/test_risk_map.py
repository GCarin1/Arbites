"""Mapa de Risco — churn de git + commits que referenciam defeitos reais do
índice + pass rate de automação do repo, por arquivo, GitHub-heatmap-style.
Repositórios locais configurados em `arbites.yaml` (`risk_repos`)."""

import subprocess

import pytest
import yaml

from arbites import executions as exec_ops


def _git(repo, *args):
    subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=True,
    )


@pytest.fixture()
def git_repo(tmp_path):
    repo = tmp_path / "product-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "qa@example.com")
    _git(repo, "config", "user.name", "QA")

    (repo / "a.py").write_text("print(1)\n", encoding="utf-8")
    (repo / "b.py").write_text("print(2)\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial commit")

    (repo / "a.py").write_text("print(1)\nprint('changed')\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "tweak a.py")

    (repo / "a.py").write_text("print(1)\nprint('fixed')\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fix DF-0001: correct rounding in a.py")

    return repo


def _configure_repo(client, name, local_path):
    cfg = client.ws.config()
    cfg["risk_repos"] = [{"name": name, "local_path": str(local_path)}]
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")


def test_risk_map_ranks_files_by_churn(client, git_repo):
    _configure_repo(client, "acme/api", git_repo)
    r = client.get("/api/v1/risk-map").json()

    assert r["since_days"] == 90
    assert len(r["repos"]) == 1
    repo = r["repos"][0]
    assert repo["repo"] == "acme/api"
    assert repo["error"] is None
    assert repo["total_commits"] == 3

    files_by_path = {f["path"]: f for f in repo["files"]}
    assert files_by_path["a.py"]["churn"] == 3
    assert files_by_path["b.py"]["churn"] == 1
    # a.py deve vir primeiro (mais mudanças)
    assert repo["files"][0]["path"] == "a.py"


def test_risk_map_only_counts_commits_mentioning_a_real_defect(client, git_repo):
    d = client.post("/api/v1/defects", json={"title": "Rounding bug"}).json()
    assert d["id"] == "DF-0001"  # o commit em git_repo referencia DF-0001
    _configure_repo(client, "acme/api", git_repo)

    r = client.get("/api/v1/risk-map").json()
    files_by_path = {f["path"]: f for f in r["repos"][0]["files"]}
    assert files_by_path["a.py"]["defect_commits"] == 1
    assert files_by_path["b.py"]["defect_commits"] == 0


def test_risk_map_defect_mention_ignored_when_defect_does_not_exist(client, git_repo):
    # nenhum DF-0001 foi criado no workspace — a menção no commit é "solta"
    _configure_repo(client, "acme/api", git_repo)
    r = client.get("/api/v1/risk-map").json()
    files_by_path = {f["path"]: f for f in r["repos"][0]["files"]}
    assert files_by_path["a.py"]["defect_commits"] == 0


def test_risk_map_missing_local_path_reports_error_not_crash(client):
    _configure_repo(client, "acme/api", "C:/does/not/exist/at/all")
    r = client.get("/api/v1/risk-map").json()
    repo = r["repos"][0]
    assert repo["error"]
    assert repo["files"] == []
    assert repo["total_commits"] == 0


def test_risk_map_no_repos_configured_returns_empty_list(client):
    r = client.get("/api/v1/risk-map").json()
    assert r["repos"] == []


def test_risk_map_days_filter_excludes_older_commits(client, git_repo):
    _configure_repo(client, "acme/api", git_repo)
    r = client.get("/api/v1/risk-map", params={"days": 90}).json()
    assert r["since_days"] == 90
    assert r["repos"][0]["total_commits"] == 3  # todos os commits são "agora"


def test_risk_map_includes_automation_pass_rate_when_repo_name_matches(client, git_repo):
    _configure_repo(client, "acme/api", git_repo)
    ex = exec_ops.create(
        client.ws, "Reg . acme/api.cer", "ci", None, None, [{"id": "CT-1", "steps": []}],
        origin="github_actions",
    )
    exec_ops.set_result_status(ex, "CT-1", "passed", "ci")
    exec_ops.save(client.ws, ex)
    client.post("/api/v1/workspace/reindex")

    r = client.get("/api/v1/risk-map").json()
    assert r["repos"][0]["automation_pass_rate"] == 1.0


def test_risk_map_automation_pass_rate_is_none_without_matching_runs(client, git_repo):
    _configure_repo(client, "acme/api", git_repo)
    r = client.get("/api/v1/risk-map").json()
    assert r["repos"][0]["automation_pass_rate"] is None


def test_risk_map_respects_custom_ci_name_pattern(client, git_repo):
    """Bug real: o risk map chamava automation_report SEM o
    ci_monitoring.name_pattern configurado — com padrão customizado o pass
    rate do repo ficava None mesmo com runs verdes."""
    cfg = client.ws.config()
    cfg["risk_repos"] = [{"name": "acme/api", "local_path": str(git_repo)}]
    cfg["ci_monitoring"] = {"name_pattern": r"^(?P<repo>\S+) run$"}
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    ex = exec_ops.create(
        client.ws, "acme/api run", "ci", None, None, [{"id": "CT-1", "steps": []}],
        origin="github_actions",
    )
    exec_ops.set_result_status(ex, "CT-1", "passed", "ci")
    exec_ops.save(client.ws, ex)
    client.post("/api/v1/workspace/reindex")

    r = client.get("/api/v1/risk-map").json()
    assert r["repos"][0]["automation_pass_rate"] == 1.0


def test_risk_map_respects_custom_defect_prefix(client, tmp_path):
    """Bug real: a regex de menção a defeito era DF- hardcoded, apesar de
    id_prefixes.defect ser configurável — workspace com prefixo customizado
    nunca correlacionava commit↔defeito."""
    cfg = client.ws.config()
    cfg.setdefault("workspace", {}).setdefault("id_prefixes", {})["defect"] = "BUG"
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    repo = tmp_path / "custom-prefix-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "qa@example.com")
    _git(repo, "config", "user.name", "QA")
    (repo / "a.py").write_text("print(1)\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fix BUG-0001: rounding")

    d = client.post("/api/v1/defects", json={"title": "Rounding"}).json()
    assert d["id"] == "BUG-0001"
    cfg = client.ws.config()
    cfg["risk_repos"] = [{"name": "acme/api", "local_path": str(repo)}]
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    r = client.get("/api/v1/risk-map").json()
    files_by_path = {f["path"]: f for f in r["repos"][0]["files"]}
    assert files_by_path["a.py"]["defect_commits"] == 1
