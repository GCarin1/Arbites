"""Critérios de aceite da spec testcases (SC1)."""

from conftest import make_md


def test_create_in_chosen_folder_with_full_frontmatter(client):
    created = client.post(
        "/api/v1/testcases",
        json={
            "title": "Login com credenciais válidas",
            "type": "hybrid",
            "priority": "high",
            "status": "ready",
            "tags": ["login", "smoke"],
            "story": "ST-0012",
            "folder": "frontend/login",
            "automation": {"target": "frontend-web", "scenario_tag": "@CT-0001"},
        },
    ).json()
    assert created["path"].startswith("testcases/frontend/login/")
    assert created["automation_target"] == "frontend-web"
    assert created["scenario_tag"] == "@CT-0001"
    ws = client.ws
    text = (ws.root / created["path"]).read_text(encoding="utf-8")
    for expected in ("id: CT-0001", "type: hybrid", "story: ST-0012", "scenario_tag:"):
        assert expected in text


def test_automated_without_automation_block_is_rejected(client):
    resp = client.post(
        "/api/v1/testcases", json={"title": "Sem bloco", "type": "automated"}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "automation_required"


def test_manual_without_passos_heading_warns_not_errors(client):
    ws = client.ws
    make_md(
        ws.root / "testcases" / "CT-0500-incompleto.md",
        {"id": "CT-0500", "title": "Incompleto", "type": "manual", "status": "draft"},
        "## Objetivo\n\nsem passos\n",
    )
    client.post("/api/v1/workspace/reindex")
    # o CT entra no índice normalmente (warning, não erro)
    assert client.get("/api/v1/testcases/CT-0500").status_code == 200
    warnings = client.get("/api/v1/warnings").json()
    assert any(
        w["code"] == "missing_heading" and "CT-0500" in w["source_path"]
        for w in warnings
    )


def test_tree_mirrors_real_folder_structure(client):
    client.post("/api/v1/testcases", json={"title": "A", "folder": "frontend/login"})
    client.post("/api/v1/testcases", json={"title": "B", "folder": "backend"})
    tree = client.get("/api/v1/tree").json()
    dir_names = {d["name"] for d in tree["dirs"]}
    assert {"frontend", "backend"} <= dir_names
    frontend = next(d for d in tree["dirs"] if d["name"] == "frontend")
    assert frontend["dirs"][0]["name"] == "login"
    assert frontend["dirs"][0]["files"][0]["id"] == "CT-0001"


def test_raw_roundtrip_and_filters(client):
    created = client.post(
        "/api/v1/testcases",
        json={"title": "Filtrável", "tags": ["smoke"], "status": "ready"},
    ).json()
    raw = client.get(f"/api/v1/testcases/{created['id']}/raw")
    assert raw.status_code == 200
    assert "Scenario:" in raw.text  # template default agora é BDD (doc §1.1)

    edited = raw.text.replace("Scenario: [Nome do Cenário]", "Scenario: Editado via raw")
    client.put(f"/api/v1/testcases/{created['id']}/raw", json={"content": edited})
    assert "Editado via raw" in client.get(f"/api/v1/testcases/{created['id']}").json()["body"]

    by_tag = client.get("/api/v1/testcases", params={"tag": "smoke"}).json()
    assert [t["id"] for t in by_tag] == [created["id"]]
    by_q = client.get("/api/v1/testcases", params={"q": "Filtráv"}).json()
    assert [t["id"] for t in by_q] == [created["id"]]


def test_priority_filter_and_combined_filters(client):
    """0064: filtro `priority` novo, combinável com os demais (rastreabilidade
    do repositório de CTs — a árvore filtra pelo MESMO endpoint)."""
    high = client.post(
        "/api/v1/testcases",
        json={"title": "Crítico de login", "priority": "high", "status": "ready"},
    ).json()
    client.post(
        "/api/v1/testcases",
        json={"title": "Baixa prioridade", "priority": "low", "status": "ready"},
    )

    by_priority = client.get("/api/v1/testcases", params={"priority": "high"}).json()
    assert [t["id"] for t in by_priority] == [high["id"]]

    combined = client.get(
        "/api/v1/testcases", params={"priority": "high", "status": "ready", "q": "login"}
    ).json()
    assert [t["id"] for t in combined] == [high["id"]]

    none = client.get(
        "/api/v1/testcases", params={"priority": "high", "status": "draft"}
    ).json()
    assert none == []


def test_defects_filter_by_testcase(client):
    """0064: o painel lateral do CT lista os defeitos vinculados a ele."""
    ct = client.post("/api/v1/testcases", json={"title": "CT com bug"}).json()
    linked = client.post(
        "/api/v1/defects", json={"title": "Vinculado", "testcase": ct["id"]}
    ).json()
    client.post("/api/v1/defects", json={"title": "Solto"})

    by_ct = client.get("/api/v1/defects", params={"testcase": ct["id"]}).json()
    assert [d["id"] for d in by_ct] == [linked["id"]]


def test_testcase_results_history(client):
    """0074: histórico de resultados por CT — já passou no passado?"""
    ct = client.post("/api/v1/testcases", json={"title": "CT histórico"}).json()
    for name, status in (("Reg 1", "passed"), ("Reg 2", "failed")):
        execu = client.post(
            "/api/v1/executions", json={"name": name, "testcase_ids": [ct["id"]]}
        ).json()
        client.post(
            f"/api/v1/executions/{execu['id']}/results/{ct['id']}/status",
            json={"status": status},
        )

    history = client.get(f"/api/v1/testcases/{ct['id']}/results").json()
    assert len(history) == 2
    assert {h["status"] for h in history} == {"passed", "failed"}
    assert all(h["execution_id"] and h["execution_name"] for h in history)
    # mais recente primeiro
    assert history[0]["executed_at"] >= history[1]["executed_at"]

    assert client.get("/api/v1/testcases/CT-9999/results").status_code == 404
