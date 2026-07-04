"""Critérios de aceite da spec reporting — fórmulas sobre dataset conhecido."""

import pytest

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


@pytest.fixture()
def dataset(client):
    """1 epic, 3 stories; 2 CTs ready; 2 executions com resultados conhecidos.

    Resultados finais atuais: CT1: E1 passed, E2 failed; CT2: E1 failed,
    E2 failed (passando por retest). Logo: pass rate 1/4, bloqueio 0/4,
    retrabalho 1/4, flaky = só CT1 (passed→failed), cobertura de execução
    2/2, cobertura de requisito 1/3 (só ST com CT ready).
    """
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Autenticação"}
    ).json()
    st_covered = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Login", "epic": epic["id"]},
    ).json()
    st_draft_only = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "MFA", "epic": epic["id"]},
    ).json()
    client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Recuperar senha", "epic": epic["id"]},
    )
    ct1 = client.post(
        "/api/v1/testcases",
        json={"title": "Login ok", "status": "ready", "story": st_covered["id"], "body": TC_BODY},
    ).json()
    ct2 = client.post(
        "/api/v1/testcases",
        json={"title": "Login errado", "status": "ready", "story": st_covered["id"], "body": TC_BODY},
    ).json()
    client.post(
        "/api/v1/testcases",
        json={"title": "MFA rascunho", "status": "draft", "story": st_draft_only["id"], "body": TC_BODY},
    )

    def run(name, outcomes):
        execution = client.post(
            "/api/v1/executions",
            json={"name": name, "sprint": "S42", "testcase_ids": [ct1["id"], ct2["id"]]},
        ).json()
        for ct_id, statuses in outcomes.items():
            for status in statuses:
                client.post(
                    f"/api/v1/executions/{execution['id']}/results/{ct_id}/status",
                    json={"status": status},
                )
        return execution

    e1 = run("Regressão 1", {ct1["id"]: ["passed"], ct2["id"]: ["failed"]})
    e2 = run("Regressão 2", {ct1["id"]: ["failed"], ct2["id"]: ["retest", "failed"]})
    return {"epic": epic, "story": st_covered, "ct1": ct1, "ct2": ct2, "e1": e1, "e2": e2}


def test_requirement_coverage(client, dataset):
    m = client.get("/api/v1/metrics/coverage").json()
    assert (m["numerator"], m["denominator"]) == (1, 3)


def test_summary_formulas(client, dataset):
    m = client.get("/api/v1/metrics/summary").json()
    assert (m["execution_coverage"]["numerator"], m["execution_coverage"]["denominator"]) == (2, 2)
    assert (m["pass_rate"]["numerator"], m["pass_rate"]["denominator"]) == (1, 4)
    assert m["pass_rate"]["value"] == 0.25
    assert (m["blocked_rate"]["numerator"], m["blocked_rate"]["denominator"]) == (0, 4)
    assert (m["rework_rate"]["numerator"], m["rework_rate"]["denominator"]) == (1, 4)


def test_flaky_detects_alternation(client, dataset):
    m = client.get("/api/v1/metrics/flaky", params={"window": 5}).json()
    flagged = [f["testcase_id"] for f in m["testcases"]]
    assert flagged == [dataset["ct1"]["id"]]


def test_trend_counts_daily_events(client, dataset):
    series = client.get("/api/v1/metrics/trend", params={"days": 7}).json()
    assert len(series) == 7
    today = series[-1]
    assert today["passed"] == 1 and today["failed"] == 3 and today["blocked"] == 0


def test_sprint_filter_isolates_data(client, dataset):
    m = client.get("/api/v1/metrics/summary", params={"sprint": "OutraSprint"}).json()
    assert m["pass_rate"]["denominator"] == 0
    assert m["pass_rate"]["value"] is None  # denominador explícito, nunca escondido


def test_traceability_matrix(client, dataset):
    matrix = client.get("/api/v1/metrics/traceability").json()
    epic = matrix["epics"][0]
    stories = {s["title"]: s for s in epic["stories"]}
    login = stories["Login"]
    assert login["ct_count"] == 2
    assert login["last_status"] == "failed"  # pior entre os últimos resultados
    assert login["last_execution"] == dataset["e2"]["id"]
    mfa = stories["MFA"]
    assert mfa["covered"] and mfa["last_status"] is None  # CT draft, sem execução
    senha = stories["Recuperar senha"]
    assert not senha["covered"]  # sem cobertura
