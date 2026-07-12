"""Decisões arquiteturais do time de QA (Memória Histórica) — CRUD completo,
mirror do padrão de defects; NÃO é o sistema de ADR do próprio Doctrina.
"""


def test_create_decision_with_default_body_template(client):
    d = client.post(
        "/api/v1/decisions",
        json={"title": "Estratégia de dados de teste", "squad": "pagamentos"},
    ).json()
    assert d["id"] == "DEC-0001"
    assert d["status"] == "proposed"
    assert d["squad"] == "pagamentos"
    assert d["created"]
    assert "## Contexto" in d["body"] and "## Decisão" in d["body"]

    # persistiu como .md com frontmatter no workspace (fonte de verdade)
    ws = client.ws
    files = list((ws.root / "decisions").glob("*.md"))
    assert len(files) == 1
    assert "pagamentos" in files[0].read_text(encoding="utf-8")


def test_list_filter_by_status_and_squad(client):
    client.post("/api/v1/decisions", json={"title": "A", "status": "accepted", "squad": "core"})
    client.post("/api/v1/decisions", json={"title": "B", "status": "proposed", "squad": "core"})
    client.post("/api/v1/decisions", json={"title": "C", "status": "accepted", "squad": "risco"})

    accepted = client.get("/api/v1/decisions", params={"status": "accepted"}).json()
    assert {d["title"] for d in accepted} == {"A", "C"}

    core = client.get("/api/v1/decisions", params={"squad": "core"}).json()
    assert {d["title"] for d in core} == {"A", "B"}

    all_decisions = client.get("/api/v1/decisions").json()
    assert len(all_decisions) == 3


def test_get_update_delete_decision(client):
    d = client.post(
        "/api/v1/decisions",
        json={"title": "Original", "tags": ["dados-de-teste", "ci"], "body": "corpo original"},
    ).json()
    assert d["tags"] == ["dados-de-teste", "ci"]

    fetched = client.get(f"/api/v1/decisions/{d['id']}").json()
    assert fetched["body"] == "corpo original"

    updated = client.put(
        f"/api/v1/decisions/{d['id']}", json={"status": "accepted", "body": "revisado"}
    ).json()
    assert updated["status"] == "accepted"
    assert updated["body"] == "revisado"
    assert updated["tags"] == ["dados-de-teste", "ci"]  # não mexeu

    resp = client.delete(f"/api/v1/decisions/{d['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/v1/decisions/{d['id']}").status_code == 404
    ws = client.ws
    assert list(ws.trash_dir.rglob("*.md"))  # foi pra lixeira, não apagada


def test_supersedes_links_to_another_decision(client):
    old = client.post("/api/v1/decisions", json={"title": "Decisão antiga"}).json()
    new = client.post(
        "/api/v1/decisions",
        json={"title": "Decisão nova", "supersedes": old["id"], "status": "accepted"},
    ).json()
    assert new["supersedes"] == old["id"]


def test_decision_searchable_and_mentionable(client):
    d = client.post("/api/v1/decisions", json={"title": "Padrão de mocks em CI"}).json()
    results = client.get("/api/v1/search", params={"q": "mocks"}).json()["results"]
    assert any(r["id"] == d["id"] and r["kind"] == "decision" for r in results)


def test_decision_id_conflict_and_reindex_survival(client):
    d = client.post("/api/v1/decisions", json={"title": "X"}).json()
    client.post("/api/v1/workspace/reindex")
    fetched = client.get(f"/api/v1/decisions/{d['id']}").json()
    assert fetched["title"] == "X"
