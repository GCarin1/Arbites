"""Critérios de aceite da spec workspace-core (SC1)."""

from conftest import make_md


def test_get_workspace_returns_config_and_index_status(client):
    resp = client.get("/api/v1/workspace")
    assert resp.status_code == 200
    data = resp.json()
    assert data["config"]["workspace"]["id_prefixes"]["testcase"] == "CT"
    assert data["index"]["last_reindex"] is not None


def test_create_testcase_consumes_counter_and_writes_md(client):
    first = client.post("/api/v1/testcases", json={"title": "Login válido"}).json()
    second = client.post("/api/v1/testcases", json={"title": "Login inválido"}).json()
    assert first["id"] == "CT-0001"
    assert second["id"] == "CT-0002"
    ws = client.ws
    files = list((ws.root / "testcases").glob("*.md"))
    assert len(files) == 2
    assert any("CT-0001" in f.read_text(encoding="utf-8") for f in files)


def test_delete_moves_to_trash_and_removes_from_index(client):
    created = client.post("/api/v1/testcases", json={"title": "Descartável"}).json()
    resp = client.delete(f"/api/v1/testcases/{created['id']}")
    assert resp.status_code == 204
    ws = client.ws
    assert not list((ws.root / "testcases").glob("*.md"))
    assert list(ws.trash_dir.glob("*.md")), "arquivo deve ir para .arbites/trash/"
    assert client.get(f"/api/v1/testcases/{created['id']}").status_code == 404


def test_delete_index_db_and_reindex_loses_nothing(ws):
    from fastapi.testclient import TestClient

    from arbites.api import create_app
    from arbites.indexer import connect, reindex_full

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.post("/api/v1/requirements", json={"kind": "epic", "title": "Autenticação"})
        client.post("/api/v1/testcases", json={"title": "Login válido"})
    # app encerrado (conexão fechada): simula perda total do índice
    ws.index_db_path.unlink(missing_ok=False)
    conn = connect(ws)
    reindex_full(ws, conn)
    assert conn.execute("SELECT COUNT(*) c FROM requirements").fetchone()["c"] == 1
    assert conn.execute("SELECT COUNT(*) c FROM testcases").fetchone()["c"] == 1


def test_manual_id_adjusts_counter_on_reindex(ws, indexed):
    from arbites.indexer import reindex_full

    make_md(
        ws.root / "testcases" / "CT-0042-feito-a-mao.md",
        {"id": "CT-0042", "title": "Feito à mão", "type": "manual", "status": "draft"},
        "## Passos\n\n1. Passo\n\n## Resultado esperado\n\nOk\n",
    )
    reindex_full(ws, indexed)
    assert ws.next_id("testcase") == "CT-0043"
