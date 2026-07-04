"""SC2 — regressão manual completa de ~20 CTs com evidências e defeito
vinculado, sem tocar em outro sistema (spec executions, critério 1)."""

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir\n2. Agir\n3. Conferir\n\n"
    "## Resultado esperado\n\nOk.\n"
)


def test_full_manual_regression_20_cts(client):
    # arrange: epic, story e 20 CTs ready
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Autenticação"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Login válido", "epic": epic["id"]},
    ).json()
    ct_ids = []
    for i in range(20):
        ct = client.post(
            "/api/v1/testcases",
            json={
                "title": f"Caso {i + 1}",
                "status": "ready",
                "story": story["id"],
                "body": TC_BODY,
            },
        ).json()
        ct_ids.append(ct["id"])

    # cria a execution da regressão
    execution = client.post(
        "/api/v1/executions",
        json={
            "name": "Regressão Sprint 42",
            "sprint": "Sprint 42",
            "environment": "homolog",
            "testcase_ids": ct_ids,
            "owner": "carini",
        },
    ).json()
    exec_id = execution["id"]
    assert len(execution["results"]) == 20

    # executa: 19 passam (com steps marcados), 1 falha com evidência
    for ct_id in ct_ids[:19]:
        for step in (1, 2, 3):
            client.post(
                f"/api/v1/executions/{exec_id}/results/{ct_id}/steps/{step}",
                json={"status": "passed", "who": "carini"},
            )
        client.post(
            f"/api/v1/executions/{exec_id}/results/{ct_id}/status",
            json={"status": "passed", "who": "carini"},
        )

    failed_ct = ct_ids[19]
    client.post(
        f"/api/v1/executions/{exec_id}/results/{failed_ct}/steps/2",
        json={"status": "failed", "who": "carini"},
    )
    client.post(
        f"/api/v1/executions/{exec_id}/results/{failed_ct}/status",
        json={"status": "failed", "who": "carini", "comment": "erro 500 no login"},
    )
    evidence = client.post(
        f"/api/v1/executions/{exec_id}/results/{failed_ct}/evidences",
        files={"file": ("erro-500.png", b"png-bytes", "image/png")},
        data={"note": "stacktrace na tela"},
    ).json()
    assert evidence["sha256"]

    # defeito vinculado ao resultado failed
    defect = client.post(
        "/api/v1/defects",
        json={
            "title": "Erro 500 ao logar",
            "severity": "high",
            "testcase": failed_ct,
            "execution": exec_id,
            "external_key": "PROJ-999",
        },
    ).json()
    assert defect["id"] == "DF-0001"

    # fecha a execution e confere o estado final
    closed = client.post(f"/api/v1/executions/{exec_id}/close").json()
    assert closed["status"] == "closed"
    statuses = [r["status"] for r in closed["results"]]
    assert statuses.count("passed") == 19 and statuses.count("failed") == 1
    failed_result = next(r for r in closed["results"] if r["testcase_id"] == failed_ct)
    assert failed_result["defects"] == ["DF-0001"]
    assert len(failed_result["evidences"]) == 1
    # history registra criação, steps, resultados, evidência, defeito e fechamento
    events = {e["event"] for e in closed["history"]}
    assert {"created", "step", "result", "evidence", "defect", "closed"} <= events
