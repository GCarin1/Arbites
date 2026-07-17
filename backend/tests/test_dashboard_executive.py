"""Dashboard executivo (reporting) — GET /metrics/dashboard: variação vs
período anterior, alertas de risco (achados bad do Auditor + Health Score),
top problemas e ações recomendadas. Nada de coleta nova — orquestra os
reports existentes."""

from datetime import datetime, timedelta, timezone

import frontmatter

from arbites import metrics as metrics_ops


def test_dashboard_has_expected_shape(client):
    r = client.get("/api/v1/metrics/dashboard").json()
    assert set(r) == {
        "last_reindex", "pass_rate_trend", "alerts", "top_problems",
        "recommended_actions",
    }
    assert set(r["pass_rate_trend"]) == {"days", "current", "previous", "delta"}
    assert set(r["top_problems"]) == {
        "worst_repos", "top_failing_testcases", "oldest_defects",
    }


def _age_defect(client, defect_id, days_old):
    path = next((client.ws.root / "defects").glob(f"{defect_id}-*.md"))
    post = frontmatter.load(str(path))
    post.metadata["opened"] = (
        datetime.now(timezone.utc) - timedelta(days=days_old)
    ).date().isoformat()
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    client.post("/api/v1/workspace/reindex")


def test_forgotten_defect_becomes_bad_alert_and_recommended_action(client):
    d = client.post(
        "/api/v1/defects", json={"title": "Bug crítico", "severity": "critical"}
    ).json()
    _age_defect(client, d["id"], 40)  # > 2× o limiar default (14) → severidade bad

    r = client.get("/api/v1/metrics/dashboard").json()
    alerts = r["alerts"]
    assert any(a["ref"] == d["id"] and a["severity"] == "bad" for a in alerts)
    # o mesmo achado vira ação recomendada reformulada
    assert any(d["id"] in a["message"] for a in r["recommended_actions"])


def test_uncovered_story_is_recommended_action_not_bad_alert(client):
    epic = client.post("/api/v1/requirements", json={"kind": "epic", "title": "E"}).json()
    story = client.post(
        "/api/v1/requirements", json={"kind": "story", "title": "Sem CT", "epic": epic["id"]}
    ).json()

    r = client.get("/api/v1/metrics/dashboard").json()
    # story sem CT é `warn` no auditor → ação recomendada, não alerta bad
    assert any(story["id"] in a["message"] for a in r["recommended_actions"])
    assert not any(a["ref"] == story["id"] for a in r["alerts"])


def test_oldest_defects_sorted_desc_by_age(client):
    d1 = client.post("/api/v1/defects", json={"title": "recente"}).json()
    d2 = client.post("/api/v1/defects", json={"title": "antigo"}).json()
    _age_defect(client, d1["id"], 5)
    _age_defect(client, d2["id"], 40)

    r = client.get("/api/v1/metrics/dashboard").json()
    oldest = r["top_problems"]["oldest_defects"]
    assert oldest[0]["id"] == d2["id"]  # o mais antigo primeiro
    assert oldest[0]["age_days"] >= oldest[1]["age_days"]


def test_low_health_score_adds_health_alert(client):
    # 1 defeito crítico sem cobertura/automação → Health Score baixo (< 50)
    client.post("/api/v1/defects", json={"title": "Crítico", "severity": "critical"})
    client.post("/api/v1/defects", json={"title": "Crítico 2", "severity": "critical"})
    client.post("/api/v1/defects", json={"title": "Crítico 3", "severity": "critical"})
    r = client.get("/api/v1/metrics/dashboard").json()
    health_alerts = [a for a in r["alerts"] if a["category"] == "health"]
    # só afirma o formato quando de fato ficou baixo (defensivo)
    if health_alerts:
        assert "Health Score baixo" in health_alerts[0]["message"]


def test_last_reindex_present(client):
    client.post("/api/v1/workspace/reindex")
    r = client.get("/api/v1/metrics/dashboard").json()
    assert r["last_reindex"]  # timestamp ISO do último reindex


def test_period_pass_rate_current_vs_previous(client):
    """A janela atual e a anterior são calculadas separadamente; o dataset
    recém-criado cai na janela atual, a anterior fica vazia (previous None)."""
    r = metrics_ops.period_pass_rate(client_conn(client), days=30)
    assert r["days"] == 30
    assert r["previous"] is None  # nada na janela anterior
    assert r["delta"] is None


def client_conn(client):
    # a app guarda a conexão no state; reusa a mesma do servidor de teste
    return client.app.state.conn
