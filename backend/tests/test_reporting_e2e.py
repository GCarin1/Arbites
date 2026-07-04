"""SC3 — reporte de sprint com drill-down até o arquivo de evidência
(spec reporting, critério 1; spec defects, critério 2)."""

TC_BODY = "## Passos\n\n1. Abrir\n2. Conferir\n\n## Resultado esperado\n\nok\n"


def test_sprint_report_with_drilldown_to_evidence(client):
    # sprint com epic, story, 3 CTs, execução com falha + evidência + defeito
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Autenticação"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Login válido", "epic": epic["id"]},
    ).json()
    ct_ids = [
        client.post(
            "/api/v1/testcases",
            json={"title": f"Caso {i}", "status": "ready", "story": story["id"], "body": TC_BODY},
        ).json()["id"]
        for i in range(3)
    ]
    execution = client.post(
        "/api/v1/executions",
        json={"name": "Regressão S42", "sprint": "S42", "testcase_ids": ct_ids},
    ).json()
    for ct_id in ct_ids[:2]:
        client.post(
            f"/api/v1/executions/{execution['id']}/results/{ct_id}/status",
            json={"status": "passed"},
        )
    failed = ct_ids[2]
    client.post(
        f"/api/v1/executions/{execution['id']}/results/{failed}/status",
        json={"status": "failed"},
    )
    evidence_bytes = b"screenshot-do-erro"
    client.post(
        f"/api/v1/executions/{execution['id']}/results/{failed}/evidences",
        files={"file": ("erro.png", evidence_bytes, "image/png")},
    )
    defect = client.post(
        "/api/v1/defects",
        json={"title": "Erro no login", "testcase": failed, "execution": execution["id"]},
    ).json()
    client.post(f"/api/v1/executions/{execution['id']}/close")

    # o reporte: summary + trend + matriz, filtrados pela sprint
    summary = client.get("/api/v1/metrics/summary", params={"sprint": "S42"}).json()
    assert summary["pass_rate"]["numerator"] == 2
    assert summary["pass_rate"]["denominator"] == 3
    trend = client.get("/api/v1/metrics/trend", params={"days": 7, "sprint": "S42"}).json()
    assert trend[-1]["passed"] == 2 and trend[-1]["failed"] == 1

    matrix = client.get(
        "/api/v1/metrics/traceability", params={"sprint": "S42"}
    ).json()
    row = matrix["epics"][0]["stories"][0]
    assert row["last_status"] == "failed"
    assert row["evidence_count"] == 1
    assert [d["id"] for d in row["defects"]] == [defect["id"]]  # defeito na matriz

    # drill-down: da matriz até o ARQUIVO da evidência
    ct_row = next(t for t in row["testcases"] if t["id"] == failed)
    assert ct_row["last_result"]["execution_id"] == execution["id"]
    downloaded = client.get(
        f"/api/v1/executions/{execution['id']}/results/{failed}/evidences/0/file"
    )
    assert downloaded.status_code == 200
    assert downloaded.content == evidence_bytes

    # e os dois formatos de export saem sem erro
    assert client.get(
        "/api/v1/metrics/traceability/export", params={"format": "md", "sprint": "S42"}
    ).status_code == 200
    assert client.get(
        "/api/v1/metrics/traceability/export", params={"format": "pdf", "sprint": "S42"}
    ).status_code == 200
