"""Pacote de Agente (0094) — ZIP com AGENTS.md + specs/ + skills/ do escopo,
pronto para colar num repositório. Mesma fonte do context-pack."""

import io
import zipfile

TC_BODY = (
    "# language: pt\nFuncionalidade: Login\n\n"
    "  Cenário: senha válida\n    Dado um usuário\n    Quando informa a senha\n"
    "    Então entra\n"
)


def _names(resp) -> list[str]:
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    return zf.namelist()


def _read(resp, name) -> str:
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    return zf.read(name).decode("utf-8")


def _dataset(client):
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Login"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Recuperar senha", "epic": epic["id"]},
    ).json()
    ct = client.post(
        "/api/v1/testcases",
        json={"title": "Envia link", "story": story["id"], "body": TC_BODY},
    ).json()
    client.post(
        "/api/v1/decisions",
        json={"title": "Tokens expiram em 30min", "status": "accepted",
              "body": "Nunca aceitar token antigo."},
    )
    return epic, story, ct


def test_agent_pack_requires_scope(client):
    resp = client.get("/api/v1/agent-pack")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "scope_required"


def test_agent_pack_zip_has_agents_md_specs_and_skills(client):
    _epic, story, ct = _dataset(client)
    client.post(
        "/api/v1/defects",
        json={"title": "Token não expira", "testcase": ct["id"],
              "root_cause": "comparação de data errada",
              "fix": "usar timezone-aware", "prevention": "sempre UTC"},
    )

    resp = client.get("/api/v1/agent-pack", params={"story": story["id"]})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    names = _names(resp)

    assert "AGENTS.md" in names
    assert any(n.startswith("specs/") and story["id"] in n for n in names)
    assert any(n.startswith("skills/") for n in names)

    agents = _read(resp, "AGENTS.md")
    assert "Tokens expiram em 30min" in agents  # decisão aceita vira convenção

    spec_name = next(n for n in names if n.startswith("specs/"))
    spec = _read(resp, spec_name)
    assert ct["id"] in spec
    assert "Cenário: senha válida" in spec  # corpo BDD do CT incluído

    skill_name = next(n for n in names if n.startswith("skills/"))
    skill = _read(resp, skill_name)
    assert "comparação de data errada" in skill  # causa raiz → when
    assert "usar timezone-aware" in skill  # fix → procedure
    assert "sempre UTC" in skill  # prevention → anti-pattern


def test_agent_pack_claude_layout_changes_skill_path(client):
    _epic, story, ct = _dataset(client)
    client.post(
        "/api/v1/defects",
        json={"title": "Bug X", "testcase": ct["id"], "root_cause": "causa"},
    )

    resp = client.get(
        "/api/v1/agent-pack", params={"story": story["id"], "layout": "claude"}
    )
    names = _names(resp)
    assert "AGENTS.md" in names
    assert any(n.startswith(".claude/skills/") and n.endswith("/SKILL.md") for n in names)
    assert not any(n.startswith("skills/") for n in names)


def test_agent_pack_skill_only_for_defects_with_root_cause(client):
    _epic, story, ct = _dataset(client)
    # defeito SEM causa raiz → não vira skill
    client.post(
        "/api/v1/defects", json={"title": "Sem causa", "testcase": ct["id"]}
    )
    resp = client.get("/api/v1/agent-pack", params={"story": story["id"]})
    assert not any(n.startswith("skills/") for n in _names(resp))


def test_agent_pack_invalid_layout_422(client):
    _epic, story, _ct = _dataset(client)
    resp = client.get(
        "/api/v1/agent-pack", params={"story": story["id"], "layout": "xpto"}
    )
    assert resp.status_code == 422
