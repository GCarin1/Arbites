"""Context Pack — bundle Markdown único (RAG-ready) com requisitos, casos de
teste, defeitos e decisões de um escopo (epic/story/squad), para agentes de
IA externos (Cursor, Claude Code, Codex, Roo Code, Aider, etc.)."""

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def _build_dataset(client, squad=None):
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Pagamentos"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={
            "kind": "story", "title": "Checkout com PIX", "epic": epic["id"],
            "squad": squad, "body": "## Descrição\n\nComo cliente quero pagar com PIX.",
        },
    ).json()
    ct = client.post(
        "/api/v1/testcases",
        json={
            "title": "Validar pagamento PIX", "status": "ready", "story": story["id"],
            "squad": squad, "body": TC_BODY,
        },
    ).json()
    defect = client.post(
        "/api/v1/defects",
        json={
            "title": "PIX falha com valor decimal", "severity": "high",
            "testcase": ct["id"], "root_cause": "arredondamento incorreto",
            "fix": "usar Decimal em vez de float",
        },
    ).json()
    return epic, story, ct, defect


def test_context_pack_requires_a_scope(client):
    resp = client.get("/api/v1/context-pack")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "scope_required"


def test_context_pack_by_story_includes_story_ct_and_defect_bodies(client):
    _epic, story, ct, defect = _build_dataset(client)

    resp = client.get("/api/v1/context-pack", params={"story": story["id"]})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    body = resp.text

    assert story["id"] in body and "Checkout com PIX" in body
    assert "Como cliente quero pagar com PIX" in body
    assert ct["id"] in body and "Validar pagamento PIX" in body
    assert "## Passos" in body  # corpo do CT incluído
    assert defect["id"] in body and "arredondamento incorreto" in body
    assert "usar Decimal em vez de float" in body


def test_context_pack_by_epic_includes_all_its_stories(client):
    epic, story, _ct, _defect = _build_dataset(client)
    other_story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Outra story", "epic": epic["id"]},
    ).json()

    body = client.get("/api/v1/context-pack", params={"epic": epic["id"]}).text
    assert story["id"] in body
    assert other_story["id"] in body


def test_context_pack_by_squad_includes_decisions(client):
    _epic, story, _ct, _defect = _build_dataset(client, squad="pagamentos")
    client.post(
        "/api/v1/decisions",
        json={
            "title": "Usar Decimal para valores monetários", "squad": "pagamentos",
            "status": "accepted", "body": "Nunca usar float para dinheiro.",
        },
    )

    body = client.get("/api/v1/context-pack", params={"squad": "pagamentos"}).text
    assert story["id"] in body
    assert "Usar Decimal para valores monetários" in body
    assert "Nunca usar float para dinheiro" in body


def test_context_pack_empty_scope_says_nothing_found(client):
    body = client.get("/api/v1/context-pack", params={"epic": "EP-9999"}).text
    assert "Nenhum requisito encontrado" in body


def test_context_pack_story_not_in_scope_is_excluded(client):
    epic, story, _ct, _defect = _build_dataset(client)
    other = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Não deve aparecer", "epic": epic["id"]},
    ).json()

    body = client.get("/api/v1/context-pack", params={"story": story["id"]}).text
    assert story["id"] in body
    assert other["id"] not in body


# ----------------------------------------------------------------- 0079


def test_context_pack_json_format_returns_counts_and_markdown(client):
    _epic, story, ct, defect = _build_dataset(client)
    data = client.get(
        "/api/v1/context-pack", params={"story": story["id"], "format": "json"}
    ).json()

    assert data["scope"] == {"story": story["id"]}
    assert data["counts"]["requirements"] >= 1
    assert data["counts"]["testcases"] == 1
    assert data["counts"]["defects"] == 1
    assert data["bytes"] == len(data["markdown"].encode("utf-8"))
    assert ct["id"] in data["markdown"]
    assert defect["id"] in data["markdown"]


def test_context_pack_section_toggles_remove_sections(client):
    _epic, story, ct, defect = _build_dataset(client)
    params = {
        "story": story["id"], "format": "json",
        "testcases": "false", "defects": "false",
    }
    data = client.get("/api/v1/context-pack", params=params).json()

    assert data["counts"]["testcases"] == 0
    assert data["counts"]["defects"] == 0
    assert ct["id"] not in data["markdown"]
    assert defect["id"] not in data["markdown"]
    # a story em si continua no pack
    assert story["id"] in data["markdown"]


def test_context_pack_includes_accepted_decisions_without_squad(client):
    _epic, story, _ct, _defect = _build_dataset(client)
    dec = client.post(
        "/api/v1/decisions",
        json={"title": "Usar UTC em timestamps", "status": "accepted",
              "body": "Sempre gravar em UTC."},
    ).json()

    # sem squad, mas com decisions ligado (default) → ADRs aceitas entram
    data = client.get(
        "/api/v1/context-pack", params={"story": story["id"], "format": "json"}
    ).json()
    assert data["counts"]["decisions"] >= 1
    assert dec["id"] in data["markdown"]
    assert "Usar UTC em timestamps" in data["markdown"]

    # com decisions=false, some
    off = client.get(
        "/api/v1/context-pack",
        params={"story": story["id"], "format": "json", "decisions": "false"},
    ).json()
    assert off["counts"]["decisions"] == 0
    assert dec["id"] not in off["markdown"]


def test_context_pack_last_result_appends_latest_status(client):
    _epic, story, ct, _defect = _build_dataset(client)
    execu = client.post(
        "/api/v1/executions", json={"name": "Regressão", "testcase_ids": [ct["id"]]}
    ).json()
    client.post(
        f"/api/v1/executions/{execu['id']}/results/{ct['id']}/status",
        json={"status": "passed"},
    )

    off = client.get(
        "/api/v1/context-pack", params={"story": story["id"], "format": "json"}
    ).json()
    assert "Último resultado" not in off["markdown"]

    on = client.get(
        "/api/v1/context-pack",
        params={"story": story["id"], "format": "json", "last_result": "true"},
    ).json()
    assert "Último resultado: passed" in on["markdown"]
