"""Critérios de aceite EARS na story (0091): parse + índice + lint
determinístico. O lint é opt-in pela seção `## Critérios de aceite`."""

from arbites.parser import ears_form, parse_criteria

GOOD_BODY = (
    "## Descrição\n\nComo usuário quero recuperar a senha.\n\n"
    "## Critérios de aceite\n\n"
    "- [EARS-1] The system shall enviar um link de redefinição por e-mail.\n"
    "- [EARS-2] When o e-mail não está cadastrado, the system shall mostrar"
    " mensagem genérica.\n"
    "- [EARS-3] o link expira em 30 minutos.\n"  # sem forma EARS
)


def test_ears_form_detection():
    assert ears_form("The system shall enviar X.") == "ubiquitous"
    assert ears_form("When algo acontece, the system shall reagir.") == "event"
    assert ears_form("While ativo, the system shall manter Y.") == "state"
    assert ears_form("The system shall not gravar Z.") == "unwanted"
    assert ears_form("Where houver provider, the system may usar IA.") == "optional"
    assert ears_form("o link expira em 30 minutos") is None  # sem modal


def test_parse_criteria_extracts_only_from_section():
    crits = parse_criteria(GOOD_BODY)
    assert [c["ears_id"] for c in crits] == ["EARS-1", "EARS-2", "EARS-3"]
    assert crits[0]["form"] == "ubiquitous"
    assert crits[1]["form"] == "event"
    assert crits[2]["form"] is None
    # a linha de descrição fora da seção não vira critério
    assert all("recuperar a senha" not in c["text"] for c in crits)


def test_criteria_indexed_and_exposed(client):
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Recuperar senha", "body": GOOD_BODY},
    ).json()
    crits = client.get(f"/api/v1/requirements/{story['id']}/criteria").json()
    assert [c["ears_id"] for c in crits] == ["EARS-1", "EARS-2", "EARS-3"]
    assert crits[0]["form"] == "ubiquitous"
    assert crits[2]["form"] is None


def test_lint_warns_no_form_and_vague_term(client):
    body = (
        "## Critérios de aceite\n\n"
        "- [EARS-1] a tela deve carregar rápido.\n"  # modal 'deve' + termo vago
        "- [EARS-2] o botão fica azul.\n"  # sem forma EARS
    )
    client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Perf", "body": body},
    )
    warns = client.get("/api/v1/warnings").json()
    codes = [w["code"] for w in warns]
    assert "ears_vague" in codes  # 'rápido'
    assert "ears_no_form" in codes  # EARS-2 sem modal


def test_legacy_story_without_section_has_no_ears_warning(client):
    client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Antiga", "body": "## Descrição\n\ntexto rápido aqui."},
    )
    warns = client.get("/api/v1/warnings").json()
    codes = [w["code"] for w in warns]
    assert "ears_no_form" not in codes
    assert "ears_vague" not in codes  # 'rápido' fora da seção não é lintado


def test_duplicate_criterion_warns(client):
    body = (
        "## Critérios de aceite\n\n"
        "- [EARS-1] The system shall enviar o link.\n"
        "- [EARS-2] The system shall enviar o link.\n"
    )
    client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Dup", "body": body},
    )
    codes = [w["code"] for w in client.get("/api/v1/warnings").json()]
    assert "ears_duplicate" in codes
