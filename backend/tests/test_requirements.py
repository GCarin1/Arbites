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


def test_story_chain_aggregates_cts_results_executions_and_defects(client):
    """Story 360 (0086): a cadeia completa numa chamada."""
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Pagamentos"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Checkout PIX", "epic": epic["id"]},
    ).json()
    ct_pass = client.post(
        "/api/v1/testcases", json={"title": "PIX válido", "story": story["id"]}
    ).json()
    ct_fail = client.post(
        "/api/v1/testcases", json={"title": "PIX inválido", "story": story["id"]}
    ).json()
    ct_untested = client.post(
        "/api/v1/testcases", json={"title": "PIX limite", "story": story["id"]}
    ).json()

    execu = client.post(
        "/api/v1/executions",
        json={"name": "Regressão", "testcase_ids": [ct_pass["id"], ct_fail["id"]]},
    ).json()
    client.post(
        f"/api/v1/executions/{execu['id']}/results/{ct_pass['id']}/status",
        json={"status": "passed"},
    )
    client.post(
        f"/api/v1/executions/{execu['id']}/results/{ct_fail['id']}/status",
        json={"status": "failed"},
    )
    defect = client.post(
        "/api/v1/defects",
        json={"title": "PIX rejeita centavos", "testcase": ct_fail["id"]},
    ).json()

    chain = client.get(f"/api/v1/requirements/{story['id']}/chain").json()

    assert chain["story"]["id"] == story["id"]
    assert chain["epic"]["id"] == epic["id"]

    by_id = {c["id"]: c for c in chain["testcases"]}
    assert by_id[ct_pass["id"]]["last_result"]["status"] == "passed"
    assert by_id[ct_fail["id"]]["last_result"]["status"] == "failed"
    assert by_id[ct_untested["id"]]["last_result"] is None
    # a execution que rodou os dois CTs aparece na cadeia de cada um
    assert execu["id"] in [r["execution_id"] for r in by_id[ct_pass["id"]]["executions"]]

    assert [e["id"] for e in chain["executions"]] == [execu["id"]]
    assert defect["id"] in [d["id"] for d in chain["defects"]]

    assert chain["summary"] == {
        "testcases": 3, "passing": 1, "failing": 1, "untested": 1,
        "executions": 1, "defects": 1, "evidences": 0,
    }


def test_story_chain_unknown_id_is_404(client):
    assert client.get("/api/v1/requirements/ST-9999/chain").status_code == 404


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
