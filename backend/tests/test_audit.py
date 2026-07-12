"""Agente Auditor — consolida warnings de indexação, stories sem CT, defeitos
esquecidos e automação quebrada num snapshot datado. Sem daemon: roda sob
demanda (POST /audit/run) ou lazy (GET /audit/latest, quando a última rodada
passou de `audit.auto_interval_hours`)."""

from datetime import datetime, timedelta, timezone

import frontmatter
import yaml

from arbites import executions as exec_ops


def test_audit_run_empty_workspace_has_no_findings(client):
    r = client.post("/api/v1/audit/run").json()
    assert r["total"] == 0
    assert r["findings"] == []
    assert r["trigger"] == "manual"
    assert r["id"] == "AUD-0001"


def test_audit_finds_uncovered_story(client):
    epic = client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"}).json()
    story = client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Sem CT", "epic": epic["id"]}
    ).json()

    r = client.post("/api/v1/audit/run").json()
    coverage_findings = [f for f in r["findings"] if f["category"] == "coverage"]
    assert len(coverage_findings) == 1
    assert coverage_findings[0]["code"] == "uncovered_story"
    assert coverage_findings[0]["ref"] == story["id"]


def _age_defect(client, defect_id: str, days_old: int) -> None:
    """Reescreve `opened` (frontmatter) do defeito à mão (simula defeito antigo)."""
    path = next((client.ws.root / "defects").glob(f"{defect_id}-*.md"))
    post = frontmatter.load(str(path))
    old = (datetime.now(timezone.utc) - timedelta(days=days_old)).date().isoformat()
    post.metadata["opened"] = old
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    client.post("/api/v1/workspace/reindex")


def test_audit_finds_forgotten_defect_past_default_aging(client):
    d = client.post("/api/v1/defects", json={"title": "Bug antigo", "severity": "high"}).json()
    _age_defect(client, d["id"], 30)  # default threshold = 14d, 2x = 28d -> "bad"

    r = client.post("/api/v1/audit/run").json()
    defect_findings = [f for f in r["findings"] if f["category"] == "defects"]
    assert len(defect_findings) == 1
    assert defect_findings[0]["code"] == "forgotten_defect"  # sem root_cause
    assert defect_findings[0]["severity"] == "bad"
    assert defect_findings[0]["ref"] == d["id"]


def test_audit_defect_with_lesson_is_aging_not_forgotten(client):
    d = client.post(
        "/api/v1/defects",
        json={"title": "Bug com causa", "severity": "low", "root_cause": "validação faltando"},
    ).json()
    _age_defect(client, d["id"], 20)  # < 28d -> "warn"

    r = client.post("/api/v1/audit/run").json()
    defect_findings = [f for f in r["findings"] if f["category"] == "defects"]
    assert defect_findings[0]["code"] == "aging_defect"
    assert defect_findings[0]["severity"] == "warn"


def test_audit_recent_defect_is_not_flagged(client):
    client.post("/api/v1/defects", json={"title": "Bug novo", "severity": "high"})
    r = client.post("/api/v1/audit/run").json()
    assert not [f for f in r["findings"] if f["category"] == "defects"]


def test_audit_finds_broken_automation(client):
    old_iso = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    ex = exec_ops.create(
        client.ws, "Reg . acme/api.cer", "ci", None, None, [{"id": "CT-1", "steps": []}],
        origin="github_actions",
    )
    ex["created_at"] = old_iso
    exec_ops.set_result_status(ex, "CT-1", "failed", "ci")
    exec_ops.save(client.ws, ex)
    client.post("/api/v1/workspace/reindex")

    r = client.post("/api/v1/audit/run").json()
    automation_findings = [f for f in r["findings"] if f["category"] == "automation"]
    assert len(automation_findings) == 1
    assert automation_findings[0]["code"] == "broken_automation"
    assert automation_findings[0]["ref"] == "acme/api"


def test_audit_thresholds_configurable_in_arbites_yaml(client):
    cfg = client.ws.config()
    cfg["audit"] = {"defect_aging_days": 5}
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    d = client.post("/api/v1/defects", json={"title": "Bug", "severity": "low"}).json()
    _age_defect(client, d["id"], 6)  # < default 14d, mas >= custom 5d

    r = client.post("/api/v1/audit/run").json()
    assert [f for f in r["findings"] if f["category"] == "defects"]


def test_audit_indexing_warnings_appear_as_findings(client):
    client.post("/api/v1/defects", json={"title": "Dup"})
    # duplica o ID à mão para gerar um warning de indexação real
    path = next((client.ws.root / "defects").glob("DF-0001-*.md"))
    post = frontmatter.load(str(path))
    dup_path = path.with_name("dup-" + path.name)
    dup_path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    client.post("/api/v1/workspace/reindex")

    r = client.post("/api/v1/audit/run").json()
    indexing_findings = [f for f in r["findings"] if f["category"] == "indexing"]
    assert any(f["code"] == "duplicate_id" for f in indexing_findings)


def test_audit_findings_sorted_worst_first(client):
    epic = client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"}).json()
    client.post("/api/v1/requirements", json={"kind": "story", "title": "S", "epic": epic["id"]})
    d = client.post("/api/v1/defects", json={"title": "Bug", "severity": "critical"}).json()
    _age_defect(client, d["id"], 40)  # >= 28d -> bad

    r = client.post("/api/v1/audit/run").json()
    severities = [f["severity"] for f in r["findings"]]
    order = {"bad": 0, "warn": 1, "info": 2}
    assert severities == sorted(severities, key=lambda s: order[s])
    assert severities[0] == "bad"


def test_audit_run_persists_as_markdown_doc(client):
    client.post("/api/v1/audit/run")
    files = list((client.ws.root / "audits").glob("*.md"))
    assert len(files) == 1
    assert "AUD-0001" in files[0].read_text(encoding="utf-8")


def test_audit_history_lists_past_runs(client):
    client.post("/api/v1/audit/run")
    client.post("/api/v1/audit/run")
    history = client.get("/api/v1/audit/history").json()
    assert len(history) == 2
    assert history[0]["id"] == "AUD-0002"  # mais recente primeiro


def test_audit_get_by_id(client):
    created = client.post("/api/v1/audit/run").json()
    fetched = client.get(f"/api/v1/audit/{created['id']}").json()
    assert fetched["id"] == created["id"]
    assert fetched["findings"] == created["findings"]


def test_audit_get_unknown_id_404(client):
    assert client.get("/api/v1/audit/AUD-9999").status_code == 404


def test_audit_latest_runs_automatically_when_none_exists(client):
    r = client.get("/api/v1/audit/latest").json()
    assert r["trigger"] == "auto"
    assert r["id"] == "AUD-0001"


def test_audit_latest_reuses_recent_run_without_rerunning(client):
    first = client.post("/api/v1/audit/run").json()
    second = client.get("/api/v1/audit/latest").json()
    assert second["id"] == first["id"]  # não rodou de novo, ainda "fresco"


def test_audit_latest_reruns_after_interval_expires(client):
    first = client.post("/api/v1/audit/run").json()

    # força a última rodada a parecer velha (25h atrás) reescrevendo o doc
    path = next((client.ws.root / "audits").glob(f"{first['id']}.md"))
    post = frontmatter.load(str(path))
    post.metadata["ran_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=25)
    ).isoformat()
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    client.post("/api/v1/workspace/reindex")

    second = client.get("/api/v1/audit/latest").json()
    assert second["id"] != first["id"]
    assert second["trigger"] == "auto"
