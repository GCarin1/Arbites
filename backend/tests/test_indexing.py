"""Critérios de aceite da spec indexing (SC1) — exceto Gherkin (M3)."""

from conftest import make_md

from arbites.indexer import reindex_file, reindex_full


def test_external_edit_reflects_after_incremental_reindex(client):
    created = client.post("/api/v1/testcases", json={"title": "Título original"}).json()
    ws = client.ws
    rel = created["path"]
    path = ws.root / rel

    # edição externa (Obsidian/editor): muda o título direto no arquivo
    text = path.read_text(encoding="utf-8").replace("Título original", "Título editado fora")
    path.write_text(text, encoding="utf-8")

    # o watcher chama reindex_file; aqui exercitamos o handler diretamente
    from arbites.indexer import connect

    conn = connect(ws)
    reindex_file(ws, conn, path)

    fetched = client.get(f"/api/v1/testcases/{created['id']}").json()
    assert fetched["title"] == "Título editado fora"


def test_duplicate_id_marks_both_files_as_conflict(ws, indexed):
    meta = {"id": "CT-0001", "title": "A", "type": "manual", "status": "draft"}
    body = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"
    make_md(ws.root / "testcases" / "a.md", meta, body)
    make_md(ws.root / "testcases" / "b.md", {**meta, "title": "B"}, body)
    reindex_full(ws, indexed)
    rows = indexed.execute(
        "SELECT source_path FROM warnings WHERE code = 'duplicate_id'"
    ).fetchall()
    paths = {r["source_path"] for r in rows}
    assert paths == {"testcases/a.md", "testcases/b.md"}


def test_invalid_frontmatter_is_warning_not_silent(ws, indexed):
    bad = ws.root / "testcases" / "quebrado.md"
    bad.write_text("---\nid: [unclosed\n---\ncorpo", encoding="utf-8")
    reindex_full(ws, indexed)
    codes = {r["code"] for r in indexed.execute("SELECT code FROM warnings")}
    assert "invalid_frontmatter" in codes


def test_file_deletion_removes_rows_incrementally(ws, indexed):
    path = ws.root / "testcases" / "CT-0009-x.md"
    make_md(
        path,
        {"id": "CT-0009", "title": "X", "type": "manual", "status": "draft"},
        "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n",
    )
    reindex_file(ws, indexed, path)
    assert indexed.execute("SELECT COUNT(*) c FROM testcases").fetchone()["c"] == 1
    path.unlink()
    reindex_file(ws, indexed, path)
    assert indexed.execute("SELECT COUNT(*) c FROM testcases").fetchone()["c"] == 0


def test_external_file_with_utf8_bom_is_parsed(ws, indexed):
    path = ws.root / "testcases" / "CT-0777-bom.md"
    content = (
        "---\nid: CT-0777\ntitle: Com BOM\ntype: manual\nstatus: draft\n---\n\n"
        "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"
    )
    path.write_text(content, encoding="utf-8-sig")  # Notepad/PowerShell gravam BOM
    reindex_file(ws, indexed, path)
    row = indexed.execute("SELECT title FROM testcases WHERE id = 'CT-0777'").fetchone()
    assert row is not None and row["title"] == "Com BOM"


def test_warnings_endpoint_lists_problems(client):
    ws = client.ws
    make_md(
        ws.root / "testcases" / "CT-0100-sem-passos.md",
        {"id": "CT-0100", "title": "Sem passos", "type": "manual", "status": "draft"},
        "## Objetivo\n\nsó objetivo\n",
    )
    client.post("/api/v1/workspace/reindex")
    warnings = client.get("/api/v1/warnings").json()
    assert any(w["code"] == "missing_heading" for w in warnings)
