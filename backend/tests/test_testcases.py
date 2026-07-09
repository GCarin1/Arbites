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
