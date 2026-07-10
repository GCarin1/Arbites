"""Repositório de test cases (doc de ajustes §1.1) — pastas, move, BDD, created."""

BDD_BODY = (
    "Feature: Login\n\n"
    "  Scenario: Credenciais válidas\n"
    "    Given que estou na tela de login\n"
    "    When informo credenciais válidas\n"
    "    Then vejo o dashboard\n"
)


def test_bdd_body_extracts_gherkin_steps_and_no_heading_warning(client):
    ct = client.post(
        "/api/v1/testcases", json={"title": "Login BDD", "body": BDD_BODY}
    ).json()
    # steps do CT = linhas Given/When/Then (snapshot da execution usa isso)
    execution = client.post(
        "/api/v1/executions", json={"name": "Reg", "testcase_ids": [ct["id"]]}
    ).json()
    steps = [s["text"] for s in execution["results"][0]["steps"]]
    assert steps == [
        "Given que estou na tela de login",
        "When informo credenciais válidas",
        "Then vejo o dashboard",
    ]
    # sem warning de heading ausente para corpo BDD
    warnings = client.get("/api/v1/warnings").json()
    assert not any(w["code"] == "missing_heading" for w in warnings)


def test_default_body_is_bdd_template(client):
    ct = client.post("/api/v1/testcases", json={"title": "Novo"}).json()
    assert "Feature:" in ct["body"] and "Scenario:" in ct["body"]
    assert "Given" in ct["body"]


def test_created_timestamp_indexed_and_in_tree(client):
    ct = client.post("/api/v1/testcases", json={"title": "Com data", "body": BDD_BODY}).json()
    fetched = client.get(f"/api/v1/testcases/{ct['id']}").json()
    assert fetched["created"]  # AAAA-MM-DD
    tree = client.get("/api/v1/tree").json()
    files = tree["files"] + [f for d in tree["dirs"] for f in d["files"]]
    assert any(f["id"] == ct["id"] and f["created"] for f in files)


def test_folder_create_move_and_delete(client):
    # criar pasta (aninhada, sem limite de profundidade)
    resp = client.post("/api/v1/testcases/folders", json={"path": "frontend/login/deep"})
    assert resp.status_code == 201
    tree = client.get("/api/v1/tree").json()
    assert any(d["name"] == "frontend" for d in tree["dirs"])

    # mover CT para a pasta (drag & drop)
    ct = client.post("/api/v1/testcases", json={"title": "Movível", "body": BDD_BODY}).json()
    moved = client.post(
        f"/api/v1/testcases/{ct['id']}/move", json={"folder": "frontend/login/deep"}
    ).json()
    assert moved["path"].startswith("testcases/frontend/login/deep/")
    # segue acessível pelo id
    assert client.get(f"/api/v1/testcases/{ct['id']}").status_code == 200

    # mover de volta p/ raiz
    back = client.post(f"/api/v1/testcases/{ct['id']}/move", json={"folder": ""}).json()
    assert back["path"].count("/") == 1  # testcases/<arquivo>

    # excluir pasta com conteúdo → conteúdo sai do índice
    ct2 = client.post(
        "/api/v1/testcases", json={"title": "Dentro", "body": BDD_BODY, "folder": "temp"}
    ).json()
    assert client.delete("/api/v1/testcases/folders", params={"path": "temp"}).status_code == 204
    assert client.get(f"/api/v1/testcases/{ct2['id']}").status_code == 404
    # foi para a lixeira, não apagado
    trash = list((client.ws.trash_dir).rglob("*.md"))
    assert any("dentro" in p.name.lower() for p in trash)


def test_folder_move_preserves_cts_and_reindexes_new_path(client):
    client.post("/api/v1/testcases/folders", json={"path": "origem"})
    client.post("/api/v1/testcases/folders", json={"path": "destino"})
    ct = client.post(
        "/api/v1/testcases", json={"title": "Dentro da origem", "body": BDD_BODY, "folder": "origem"}
    ).json()

    resp = client.post(
        "/api/v1/testcases/folders/move", json={"path": "origem", "dest": "destino"}
    )
    assert resp.status_code == 200
    assert resp.json()["path"] == "testcases/destino/origem"

    # o CT continua acessível pelo mesmo id, agora sob destino/origem/
    fetched = client.get(f"/api/v1/testcases/{ct['id']}").json()
    assert fetched["path"].startswith("testcases/destino/origem/")

    tree = client.get("/api/v1/tree").json()
    destino = next(d for d in tree["dirs"] if d["name"] == "destino")
    assert any(sub["name"] == "origem" for sub in destino["dirs"])
    assert not any(d["name"] == "origem" for d in tree["dirs"])  # não sobrou na raiz


def test_folder_move_into_itself_or_descendant_rejected(client):
    client.post("/api/v1/testcases/folders", json={"path": "pai/filha"})
    resp = client.post(
        "/api/v1/testcases/folders/move", json={"path": "pai", "dest": "pai/filha"}
    )
    assert resp.status_code == 422
    resp2 = client.post(
        "/api/v1/testcases/folders/move", json={"path": "pai", "dest": "pai"}
    )
    assert resp2.status_code == 422


def test_folder_move_conflict_when_dest_already_has_same_name(client):
    client.post("/api/v1/testcases/folders", json={"path": "a/login"})
    client.post("/api/v1/testcases/folders", json={"path": "b/login"})
    resp = client.post("/api/v1/testcases/folders/move", json={"path": "a/login", "dest": "b"})
    assert resp.status_code == 409


def test_folder_move_noop_when_already_at_destination(client):
    client.post("/api/v1/testcases/folders", json={"path": "solta"})
    resp = client.post("/api/v1/testcases/folders/move", json={"path": "solta", "dest": ""})
    assert resp.status_code == 200
    assert resp.json()["path"] == "testcases/solta"


def test_folder_move_traversal_guard(client):
    assert (
        client.post(
            "/api/v1/testcases/folders/move", json={"path": "../fora", "dest": ""}
        ).status_code
        == 422
    )
    client.post("/api/v1/testcases/folders", json={"path": "legit"})
    assert (
        client.post(
            "/api/v1/testcases/folders/move", json={"path": "legit", "dest": "../../etc"}
        ).status_code
        == 422
    )


def test_folder_traversal_guard(client):
    assert client.post("/api/v1/testcases/folders", json={"path": "../fora"}).status_code == 422
    ct = client.post("/api/v1/testcases", json={"title": "X", "body": BDD_BODY}).json()
    assert (
        client.post(f"/api/v1/testcases/{ct['id']}/move", json={"folder": "../../etc"}).status_code
        == 422
    )
