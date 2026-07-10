"""Heatmap de atividade estilo GitHub (perfil) — agregação diária de sinais."""

from datetime import date

from arbites import executions as exec_ops

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def test_activity_heatmap_aggregates_daily_signals(client):
    today = date.today().isoformat()
    ct1 = client.post("/api/v1/testcases", json={"title": "A", "body": TC_BODY}).json()
    ct2 = client.post("/api/v1/testcases", json={"title": "B", "body": TC_BODY}).json()
    client.post("/api/v1/defects", json={"title": "bug", "severity": "low"})
    ex = client.post(
        "/api/v1/executions",
        json={"name": "Reg", "testcase_ids": [ct1["id"], ct2["id"]]},
    ).json()
    client.post(f"/api/v1/executions/{ex['id']}/results/{ct1['id']}/status", json={"status": "passed"})
    client.post(f"/api/v1/executions/{ex['id']}/results/{ct2['id']}/status", json={"status": "failed"})

    # um run de automação hoje (origin != manual)
    aex = exec_ops.create(client.ws, "auto", "ci", None, None, [{"id": ct1["id"], "steps": []}], origin="github_actions")
    exec_ops.set_result_status(aex, ct1["id"], "passed", "ci")
    exec_ops.save(client.ws, aex)
    client.post("/api/v1/workspace/reindex")

    hm = client.get("/api/v1/metrics/activity").json()
    assert hm["from"] <= today <= hm["to"]
    day = next(d for d in hm["days"] if d["date"] == today)
    assert day["testcases"] == 2
    assert day["defects"] == 1
    assert day["executions"] == 3  # 2 no run manual + 1 no run automático (transições)
    assert day["auto_runs"] == 1
    assert day["total"] == (
        day["testcases"] + day["defects"] + day["executions"]
        + day["requirements"] + day["auto_runs"]
    )
    assert hm["totals"]["testcases"] == 2 and hm["totals"]["defects"] == 1


def test_activity_heatmap_window_starts_on_monday(client):
    hm = client.get("/api/v1/metrics/activity").json()
    assert date.fromisoformat(hm["from"]).weekday() == 0  # segunda-feira
    # ~53 semanas (371 dias + até 6 do alinhamento à segunda)
    span = (date.fromisoformat(hm["to"]) - date.fromisoformat(hm["from"])).days
    assert 370 <= span <= 377


def test_activity_heatmap_empty_when_no_activity(client):
    hm = client.get("/api/v1/metrics/activity").json()
    assert hm["days"] == []
    assert hm["totals"]["total"] == 0
    assert hm["years"] == []


def test_activity_heatmap_lists_years_with_activity(client):
    client.post("/api/v1/testcases", json={"title": "X", "body": TC_BODY})
    hm = client.get("/api/v1/metrics/activity").json()
    assert date.today().year in hm["years"]


def test_activity_heatmap_year_filter_windows_to_calendar_year(client):
    client.post("/api/v1/testcases", json={"title": "X", "body": TC_BODY})
    this_year = date.today().year
    hm = client.get("/api/v1/metrics/activity", params={"year": this_year}).json()
    assert hm["year_filter"] == this_year
    # janela alinhada à segunda, começando em/antes de 1º de janeiro
    assert date.fromisoformat(hm["from"]).weekday() == 0
    assert hm["from"] <= f"{this_year}-01-01"
    assert hm["to"] <= date.today().isoformat()
    # atividade de hoje aparece (hoje está no ano corrente)
    assert any(d["date"] == date.today().isoformat() for d in hm["days"])

    # ano passado (sem atividade) → janela do ano, sem dias
    past = client.get("/api/v1/metrics/activity", params={"year": this_year - 1}).json()
    assert past["to"] == f"{this_year - 1}-12-31"
    assert past["days"] == []
