"""Health Score — nota única 0-100 composta de cobertura/defeitos/automação/
dívida de testes, com fórmula explícita por componente e pesos configuráveis.
"""

import yaml

from arbites import executions as exec_ops

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def test_health_score_empty_workspace_has_no_score(client):
    r = client.get("/api/v1/metrics/health").json()
    assert r["score"] is None
    # sem dado, cada componente também vem None (nada escondido/inventado)
    assert all(c["value"] is None for c in r["components"].values())


def test_health_score_components_have_explicit_formula(client):
    r = client.get("/api/v1/metrics/health").json()
    for key in ("coverage", "defects", "automation", "debt"):
        assert key in r["components"]
        assert r["components"][key]["formula"]  # nunca vazio — defensável em reunião
        assert "weight" in r["components"][key]
    # pesos default somam 1.0 (renormalizados)
    assert round(sum(c["weight"] for c in r["components"].values()), 4) == 1.0


def test_health_score_defects_penalizes_by_severity(client):
    # sem cobertura/automação (fica None, não participa) — só defeitos.
    client.post("/api/v1/defects", json={"title": "Crítico", "severity": "critical"})
    r = client.get("/api/v1/metrics/health").json()
    assert r["components"]["defects"]["value"] == 75  # 100 - 25 (critical)
    # score = só o componente "defects" participou (demais são None)
    assert r["score"] == 75


def test_health_score_custom_weights_from_config(client):
    cfg = client.ws.config()
    cfg["health_score"] = {"weights": {"defects": 1.0, "coverage": 0, "automation": 0, "debt": 0}}
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    client.post("/api/v1/defects", json={"title": "Alto", "severity": "high"})
    r = client.get("/api/v1/metrics/health").json()
    assert r["components"]["defects"]["weight"] == 1.0
    assert r["score"] == 88  # 100 - 12 (high), único componente com peso > 0 e dado


def test_health_score_respects_custom_ci_name_pattern(client):
    """Bug real: health_score chamava automation_report SEM o
    ci_monitoring.name_pattern do arbites.yaml (o endpoint /metrics/automation
    passa) — com padrão customizado, todos os runs viravam unparsed e o
    componente de automação ficava None silenciosamente."""
    cfg = client.ws.config()
    cfg["ci_monitoring"] = {"name_pattern": r"^(?P<repo>\S+) run$"}
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    ex = exec_ops.create(
        client.ws, "acme/web run", "ci", None, None, [{"id": "CT-1", "steps": []}],
        origin="github_actions",
    )
    exec_ops.set_result_status(ex, "CT-1", "passed", "ci")
    exec_ops.save(client.ws, ex)
    client.post("/api/v1/workspace/reindex")

    r = client.get("/api/v1/metrics/health").json()
    assert r["components"]["automation"]["value"] == 100  # não None


def test_health_score_automation_component_from_ci_runs(client):
    ex = exec_ops.create(
        client.ws, "Reg . acme/api.cer", "ci", None, None, [{"id": "CT-1", "steps": []}],
        origin="github_actions",
    )
    exec_ops.set_result_status(ex, "CT-1", "passed", "ci")
    exec_ops.save(client.ws, ex)
    client.post("/api/v1/workspace/reindex")

    r = client.get("/api/v1/metrics/health").json()
    assert r["components"]["automation"]["value"] == 100


def test_health_score_full_dataset_combines_all_components(client):
    """1 epic, 1 story com CT ready+executado, 1 defect medium, 1 run de automação
    100% verde — todos os 4 componentes participam do score."""
    epic = client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"}).json()
    story = client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "S", "epic": epic["id"]}
    ).json()
    ct = client.post(
        "/api/v1/testcases",
        json={"title": "CT", "status": "ready", "story": story["id"], "body": TC_BODY},
    ).json()
    execu = client.post(
        "/api/v1/executions", json={"name": "Reg", "testcase_ids": [ct["id"]]}
    ).json()
    client.post(
        f"/api/v1/executions/{execu['id']}/results/{ct['id']}/status", json={"status": "passed"}
    )
    client.post("/api/v1/defects", json={"title": "Bug", "severity": "medium"})

    aex = exec_ops.create(
        client.ws, "Reg . acme/api.cer", "ci", None, None, [{"id": ct["id"], "steps": []}],
        origin="github_actions",
    )
    exec_ops.set_result_status(aex, ct["id"], "passed", "ci")
    exec_ops.save(client.ws, aex)
    client.post("/api/v1/workspace/reindex")

    r = client.get("/api/v1/metrics/health").json()
    c = r["components"]
    assert c["coverage"]["value"] == 100  # story coberta + CT executado
    assert c["defects"]["value"] == 95  # 100 - 5 (medium)
    assert c["automation"]["value"] == 100
    assert c["debt"]["value"] == 100  # sem bloqueio/retrabalho/flaky
    # score = média ponderada pelos pesos default (30/25/25/20)
    expected = round(100 * 0.30 + 95 * 0.25 + 100 * 0.25 + 100 * 0.20)
    assert r["score"] == expected
