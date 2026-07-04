"""Critérios de aceite da spec defects (SC2)."""

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


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
