"""Critérios de aceite da spec defects (SC2)."""

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def test_defects_report_aging_severity_and_squad(client):
    """M9: painel de defeitos abertos por aging/severidade/squad."""
    ct_pay = client.post(
        "/api/v1/testcases",
        json={"title": "Pix", "body": TC_BODY, "squad": "pagamentos"},
    ).json()
    ct_risco = client.post(
        "/api/v1/testcases",
        json={"title": "Risco", "body": TC_BODY, "squad": "risco"},
    ).json()
    client.post(
        "/api/v1/defects",
        json={"title": "Bug A", "severity": "critical", "testcase": ct_pay["id"]},
    )
    client.post(
        "/api/v1/defects",
        json={"title": "Bug B", "severity": "low", "testcase": ct_risco["id"]},
    )
    fixed = client.post(
        "/api/v1/defects", json={"title": "Bug C", "severity": "high"}
    ).json()
    client.put(f"/api/v1/defects/{fixed['id']}", json={"status": "fixed"})

    report = client.get("/api/v1/metrics/defects").json()
    assert report["open_count"] == 2  # o fixed não conta
    assert report["by_severity"] == {"critical": 1, "low": 1}  # ordenado
    assert report["by_squad"] == {"pagamentos": 1, "risco": 1}
    assert report["aging_buckets"]["0-7"] == 2  # criados hoje
    assert all(item["age_days"] == 0 for item in report["items"])

    # filtro por squad
    only_pag = client.get("/api/v1/metrics/defects", params={"squad": "pagamentos"}).json()
    assert only_pag["open_count"] == 1
    assert only_pag["items"][0]["title"] == "Bug A"


def test_defects_report_empty(client):
    report = client.get("/api/v1/metrics/defects").json()
    assert report["open_count"] == 0 and report["items"] == []


def test_defect_from_failed_result_links_testcase_and_execution(client):
    ct = client.post(
        "/api/v1/testcases", json={"title": "Login", "body": TC_BODY}
    ).json()
    execution = client.post(
        "/api/v1/executions",
        json={"name": "Regressão", "testcase_ids": [ct["id"]]},
    ).json()
    client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
        json={"status": "failed"},
    )
    defect = client.post(
        "/api/v1/defects",
        json={
            "title": "Falha no login",
            "severity": "high",
            "testcase": ct["id"],
            "execution": execution["id"],
        },
    ).json()
    assert defect["testcase_id"] == ct["id"]
    assert defect["execution_id"] == execution["id"]
    # arquivo .md em defects/ com frontmatter
    ws = client.ws
    files = list((ws.root / "defects").glob("*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert f"testcase: {ct['id']}" in text and f"execution: {execution['id']}" in text
    # vínculo no resultado da execution
    fetched = client.get(f"/api/v1/executions/{execution['id']}").json()
    assert fetched["results"][0]["defects"] == [defect["id"]]


def test_defect_update_and_list(client):
    defect = client.post(
        "/api/v1/defects", json={"title": "Aberto", "severity": "low"}
    ).json()
    updated = client.put(
        f"/api/v1/defects/{defect['id']}",
        json={"status": "fixed", "external_key": "PROJ-777"},
    ).json()
    assert updated["status"] == "fixed"
    assert updated["external_key"] == "PROJ-777"
    open_only = client.get("/api/v1/defects", params={"status": "open"}).json()
    assert open_only == []
    all_defects = client.get("/api/v1/defects").json()
    assert [d["id"] for d in all_defects] == [defect["id"]]
