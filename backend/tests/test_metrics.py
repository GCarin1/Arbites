"""Critérios de aceite da spec reporting — fórmulas sobre dataset conhecido."""

import yaml

import pytest

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def _set_thresholds(client, thresholds: dict) -> None:
    cfg = client.ws.config()
    cfg["metric_thresholds"] = thresholds
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")


def test_metric_thresholds_traffic_light(client, dataset):
    """M8: cada métrica recebe status ok/warn/bad conforme a meta e direção."""
    _set_thresholds(
        client,
        {
            "pass_rate": {"warn": 0.8, "bad": 0.6},  # up; valor 0.25 → bad
            "requirement_coverage": {"warn": 0.5, "bad": 0.3},  # up; 1/3≈0.33 → warn
            "blocked_rate": {"warn": 0.1, "bad": 0.2},  # down (default); 0.0 → ok
        },
    )
    m = client.get("/api/v1/metrics/summary").json()
    assert m["pass_rate"]["status"] == "bad"
    assert m["requirement_coverage"]["status"] == "warn"
    assert m["blocked_rate"]["status"] == "ok"
    assert m["blocked_rate"]["threshold"]["direction"] == "down"
    # métrica sem meta configurada → sem semáforo
    assert m["execution_coverage"]["status"] == "none"


def test_thresholds_absent_by_default(client, dataset):
    """Sem metas configuradas, nenhum semáforo (retrocompat)."""
    m = client.get("/api/v1/metrics/summary").json()
    metric_keys = [
        "requirement_coverage", "execution_coverage",
        "pass_rate", "blocked_rate", "rework_rate",
    ]
    assert all(m[k]["status"] == "none" for k in metric_keys)


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


def test_quarantine_excluded_from_pass_rate_and_counted(client, dataset):
    """0089: CT em quarentena sai do pass rate e da cobertura, mas a
    contagem aparece SEMPRE no summary com a lista para drill-down."""
    before = client.get("/api/v1/metrics/summary").json()
    assert before["pass_rate"]["denominator"] == 4  # ct1(2) + ct2(2)
    assert before["quarantine"]["count"] == 0

    # ct2 (2 resultados finais) vai para quarentena
    client.put(f"/api/v1/testcases/{dataset['ct2']['id']}", json={"quarantine": True})

    after = client.get("/api/v1/metrics/summary").json()
    # pass rate agora só considera ct1: passed(E1) + failed(E2) = 1/2
    assert (after["pass_rate"]["numerator"], after["pass_rate"]["denominator"]) == (1, 2)
    assert after["pass_rate"]["value"] == 0.5
    # cobertura de execução: ct2 sai do numerador e do denominador (só ct1 ready)
    assert after["execution_coverage"]["denominator"] == 1
    assert after["execution_coverage"]["numerator"] == 1
    # contagem visível + lista para drill-down
    assert after["quarantine"]["count"] == 1
    assert [t["testcase_id"] for t in after["quarantine"]["testcases"]] == [
        dataset["ct2"]["id"]
    ]

    # o toggle persiste no frontmatter e volta no GET do CT
    tc = client.get(f"/api/v1/testcases/{dataset['ct2']['id']}").json()
    assert tc["quarantine"] is True


def test_trend_counts_daily_events(client, dataset):
    series = client.get("/api/v1/metrics/trend", params={"days": 7}).json()
    assert len(series) == 7
    today = series[-1]
    assert today["passed"] == 1 and today["failed"] == 3 and today["blocked"] == 0


def test_trend_does_not_inflate_from_repeated_moves(client):
    """SC5: um CT arrastado por vários status no mesmo dia conta 1 vez,
    pelo status final do dia — não soma cada transição intermediária."""
    ct = client.post(
        "/api/v1/testcases",
        json={"title": "Arrastado", "status": "ready", "body": TC_BODY},
    ).json()
    execution = client.post(
        "/api/v1/executions", json={"name": "Regressão", "testcase_ids": [ct["id"]]}
    ).json()
    # simula o usuário arrastando o mesmo card por várias colunas
    for status in ["blocked", "failed", "passed", "retest", "blocked"]:
        client.post(
            f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
            json={"status": status},
        )
    series = client.get("/api/v1/metrics/trend", params={"days": 7}).json()
    today = series[-1]
    # status final do dia = blocked → conta 1 em blocked e nada nos demais
    assert (today["passed"], today["failed"], today["blocked"]) == (0, 0, 1)


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


def test_traceability_coverage_state(client):
    """0087: estado semântico por story — uncovered/untested/passing/failing."""
    epic = client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"}).json()

    def story(title):
        return client.post(
            "/api/v1/requirements",
            json={"kind": "story", "title": title, "epic": epic["id"]},
        ).json()

    def ct(story_id, title):
        return client.post(
            "/api/v1/testcases", json={"title": title, "story": story_id}
        ).json()

    def run(ct_id, status):
        ex = client.post(
            "/api/v1/executions", json={"name": "R", "testcase_ids": [ct_id]}
        ).json()
        client.post(
            f"/api/v1/executions/{ex['id']}/results/{ct_id}/status",
            json={"status": status},
        )

    s_uncovered = story("Sem CT")
    s_untested = story("Com CT sem execução")
    ct(s_untested["id"], "CT-untested")
    s_passing = story("Passando")
    run(ct(s_passing["id"], "CT-pass")["id"], "passed")
    s_failing = story("Falhando")
    run(ct(s_failing["id"], "CT-a")["id"], "passed")
    run(ct(s_failing["id"], "CT-b")["id"], "failed")  # pior = failed

    states = {}
    for e in client.get("/api/v1/metrics/traceability").json()["epics"]:
        for s in e["stories"]:
            states[s["id"]] = s["coverage_state"]

    assert states[s_uncovered["id"]] == "uncovered"
    assert states[s_untested["id"]] == "untested"
    assert states[s_passing["id"]] == "passing"
    assert states[s_failing["id"]] == "failing"


def test_traceability_criteria_coverage(client):
    """0092: contagem X/Y critérios EARS cobertos por story."""
    body = (
        "## Critérios de aceite\n\n"
        "- [EARS-1] O sistema deve enviar o link.\n"
        "- [EARS-2] O sistema deve expirar o link.\n"
    )
    epic = client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"}).json()
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Senha", "epic": epic["id"], "body": body},
    ).json()
    client.post(
        "/api/v1/testcases",
        json={"title": "CT1", "story": story["id"], "criteria": ["EARS-1"]},
    )

    matrix = client.get("/api/v1/metrics/traceability").json()
    s = matrix["epics"][0]["stories"][0]
    assert s["criteria_total"] == 2
    assert s["criteria_covered"] == 1  # só EARS-1 tem CT
