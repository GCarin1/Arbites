"""Critérios de aceite da spec xray-migration (SC4)."""

import io
import zipfile
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "xray_sample.xml"


def _upload(client, url, **data):
    return client.post(
        url,
        files={"file": ("export.xml", FIXTURE.read_bytes(), "text/xml")},
        data=data,
    )


def test_preview_lists_tests_without_touching_disk(client):
    resp = _upload(client, "/api/v1/import/xray")
    assert resp.status_code == 200
    preview = resp.json()
    assert [t["external_key"] for t in preview["tests"]] == ["QAB-101", "QAB-102", "QAB-103"]
    first = preview["tests"][0]
    assert first["action"] == "create"
    assert first["priority"] == "high"        # High → high
    assert first["labels"] == ["login", "smoke"]
    assert first["steps"] == 3
    assert first["story_key"] == "PROJ-123"
    assert "Test Repository Path" in first["unmapped"]  # campo não mapeável listado
    assert preview["stories"] == [{"external_key": "PROJ-123", "exists_locally": False}]
    # disco intocado
    ws = client.ws
    assert not list((ws.root / "testcases").rglob("*.md"))


def test_confirm_creates_cts_with_mapped_content_and_story(client):
    resp = _upload(
        client, "/api/v1/import/xray/confirm",
        folder="xray/login", create_stories="PROJ-123",
    )
    assert resp.status_code == 200
    result = resp.json()
    assert len(result["created"]) == 3
    assert result["stories_created"]["PROJ-123"].startswith("ST-")

    ws = client.ws
    ct_id = result["created"][0]["id"]
    files = list((ws.root / "testcases" / "xray" / "login").glob(f"{ct_id}-*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "external_key: QAB-101" in text
    assert "## Passos" in text and "1. Abrir a tela de login" in text
    assert "(dados: qa.user@empresa.com)" in text          # Data do step preservado
    assert "## Resultado esperado" in text
    assert "3. Dashboard exibido com nome do usuario" in text
    assert "## Pré-condições" in text
    assert "- Usuario ativo cadastrado na base de teste" in text

    # CT vinculado à story local criada (entra na matriz de cobertura)
    fetched = client.get(f"/api/v1/testcases/{ct_id}").json()
    assert fetched["story_id"] == result["stories_created"]["PROJ-123"]
    # prioridade Lowest → low
    third = client.get(f"/api/v1/testcases/{result['created'][2]['id']}").json()
    assert third["priority"] == "low"


def test_reimport_is_idempotent(client):
    first = _upload(client, "/api/v1/import/xray/confirm", folder="xray").json()
    assert len(first["created"]) == 3
    second = _upload(client, "/api/v1/import/xray/confirm", folder="xray").json()
    assert second["created"] == []
    assert {s["external_key"] for s in second["skipped"]} == {
        "QAB-101", "QAB-102", "QAB-103",
    }
    # preview após migração mostra skip
    preview = _upload(client, "/api/v1/import/xray").json()
    assert all(t["action"] == "skip (já migrado)" for t in preview["tests"])
    # nenhum arquivo duplicado
    ws = client.ws
    assert len(list((ws.root / "testcases").rglob("*.md"))) == 3


def test_invalid_xml_rejected_cleanly(client):
    resp = client.post(
        "/api/v1/import/xray",
        files={"file": ("x.xml", b"nao e xml", "text/xml")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_xml"


def test_export_markdown_zip(client):
    _upload(client, "/api/v1/import/xray/confirm", folder="xray")
    resp = client.post("/api/v1/export/markdown", params={"folder": "xray"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/zip")
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    assert len(names) == 3
    assert all(n.startswith("xray/") and n.endswith(".md") for n in names)
    content = zf.read(names[0]).decode("utf-8")
    assert "external_key:" in content  # já é o formato nativo
