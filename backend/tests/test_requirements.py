"""Critérios de aceite da spec requirements (SC1)."""


def test_create_epic_and_story_with_sequential_ids(client):
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Autenticação"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={
            "kind": "story",
            "title": "Login com credenciais válidas",
            "epic": epic["id"],
            "external_key": "PROJ-123",
        },
    ).json()
    assert epic["id"] == "EP-0001"
    assert story["id"] == "ST-0001"
    assert story["epic_id"] == "EP-0001"
    ws = client.ws
    files = list((ws.root / "requirements").glob("*.md"))
    assert len(files) == 2


def test_list_filters_by_kind_and_status(client):
    client.post("/api/v1/requirements", json={"kind": "epic", "title": "E1"})
    client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "S1", "epic": "EP-0001"},
    )
    client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "S2", "epic": "EP-0001", "status": "done"},
    )
    active_stories = client.get(
        "/api/v1/requirements", params={"kind": "story", "status": "active"}
    ).json()
    assert [r["id"] for r in active_stories] == ["ST-0001"]


def test_story_with_missing_epic_generates_warning(client):
    client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Órfã", "epic": "EP-9999"},
    )
    client.post("/api/v1/workspace/reindex")
    warnings = client.get("/api/v1/warnings").json()
    assert any(w["code"] == "missing_epic" for w in warnings)


def test_update_and_delete_requirement(client):
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Original"}
    ).json()
    updated = client.put(
        f"/api/v1/requirements/{epic['id']}", json={"title": "Renomeado"}
    ).json()
    assert updated["title"] == "Renomeado"
    assert client.delete(f"/api/v1/requirements/{epic['id']}").status_code == 204
    assert client.get(f"/api/v1/requirements/{epic['id']}").status_code == 404


def test_requirement_created_stamped_and_indexed(client):
    """Doc §1.2: data de criação registrada e exposta na listagem."""
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Com data"}
    ).json()
    assert epic["created"]  # AAAA-MM-DD
    listed = client.get("/api/v1/requirements").json()
    assert any(r["id"] == epic["id"] and r["created"] for r in listed)
