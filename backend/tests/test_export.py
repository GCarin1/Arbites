"""Critérios de aceite da spec reporting — export MD/PDF da matriz."""

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def _seed(client):
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Autenticação"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Login válido", "epic": epic["id"]},
    ).json()
    ct = client.post(
        "/api/v1/testcases",
        json={"title": "Login", "status": "ready", "story": story["id"], "body": TC_BODY},
    ).json()
    execution = client.post(
        "/api/v1/executions", json={"name": "Reg", "testcase_ids": [ct["id"]]}
    ).json()
    client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
        json={"status": "passed"},
    )
    return story


def test_markdown_export_is_confluence_pastable(client):
    story = _seed(client)
    resp = client.get("/api/v1/metrics/traceability/export", params={"format": "md"})
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    text = resp.text
    # estrutura de tabela markdown intacta (colável no Confluence)
    assert "| Epic / Story | CTs | Último resultado | Execution | Evidências | Defeitos |" in text
    assert f"| {story['id']} Login válido | 1 | passed |" in text


def test_pdf_export_returns_valid_pdf(client):
    _seed(client)
    resp = client.get("/api/v1/metrics/traceability/export", params={"format": "pdf"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:5] == b"%PDF-"
    assert len(resp.content) > 500


def test_invalid_format_rejected(client):
    resp = client.get("/api/v1/metrics/traceability/export", params={"format": "docx"})
    assert resp.status_code == 422
