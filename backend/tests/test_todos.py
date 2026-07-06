"""Critérios de aceite da spec todos (SC11)."""

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def make_ct(client, title):
    return client.post("/api/v1/testcases", json={"title": title, "body": TC_BODY}).json()


def test_todo_crud_persists_and_indexes(client):
    """SC11.1: CRUD com status/due/squad/links persistido em todos/*.md."""
    todo = client.post(
        "/api/v1/todos",
        json={
            "title": "Revisar regressão",
            "due": "2026-07-10",
            "squad": "pagamentos",
            "status": "doing",
        },
    ).json()
    assert todo["id"].startswith("TD-")
    assert todo["status"] == "doing" and todo["due"] == "2026-07-10"

    # arquivo no disco em todos/
    ws = client.ws
    files = list((ws.root / "todos").glob("*.md"))
    assert len(files) == 1 and f"due: '2026-07-10'" in files[0].read_text(encoding="utf-8")

    # update: concluir
    updated = client.put(f"/api/v1/todos/{todo['id']}", json={"status": "done"}).json()
    assert updated["status"] == "done"

    # delete → some da listagem
    assert client.delete(f"/api/v1/todos/{todo['id']}").status_code == 204
    assert client.get("/api/v1/todos").json() == []


def test_todo_filter_by_status_and_period(client):
    """SC11.2: filtro por status e por período (due)."""
    client.post("/api/v1/todos", json={"title": "A", "due": "2026-07-05", "status": "open"})
    client.post("/api/v1/todos", json={"title": "B", "due": "2026-07-20", "status": "blocked"})
    client.post("/api/v1/todos", json={"title": "C", "status": "open"})  # sem due

    blocked = client.get("/api/v1/todos", params={"status": "blocked"}).json()
    assert [t["title"] for t in blocked] == ["B"]

    window = client.get(
        "/api/v1/todos", params={"due_from": "2026-07-01", "due_to": "2026-07-10"}
    ).json()
    assert [t["title"] for t in window] == ["A"]


def test_done_todos_remain_in_history(client):
    """SC11.3: todos done permanecem consultáveis."""
    todo = client.post("/api/v1/todos", json={"title": "Feito", "status": "open"}).json()
    client.put(f"/api/v1/todos/{todo['id']}", json={"status": "done"})
    done = client.get("/api/v1/todos", params={"status": "done"}).json()
    assert [t["title"] for t in done] == ["Feito"]


def test_todo_links_resolve_titles(client):
    """SC11.4: links para CT/execução/story resolvem o título."""
    ct = make_ct(client, "Login ok")
    execution = client.post(
        "/api/v1/executions", json={"name": "Regressão S1", "testcase_ids": [ct["id"]]}
    ).json()
    todo = client.post(
        "/api/v1/todos",
        json={"title": "Rodar login", "links": [ct["id"], execution["id"], "ST-9999"]},
    ).json()
    by_id = {link["id"]: link for link in todo["links"]}
    assert by_id[ct["id"]]["title"] == "Login ok" and by_id[ct["id"]]["kind"] == "testcase"
    assert by_id[execution["id"]]["title"] == "Regressão S1"
    assert by_id["ST-9999"]["title"] is None  # link pendente, não quebra

    # filtro por link
    linked = client.get("/api/v1/todos", params={"link": ct["id"]}).json()
    assert [t["title"] for t in linked] == ["Rodar login"]
