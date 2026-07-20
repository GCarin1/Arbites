"""Pacote de Agente (0094) — exporta o contexto de um escopo como um PACOTE
DE REPOSITÓRIO pronto para colar num projeto, em vez de um Markdown de chat
(esse é o context-pack). Gera:

- `AGENTS.md` — convenções derivadas das decisões arquiteturais ACEITAS +
  glossário dos artefatos + mapa do pacote.
- `specs/<story>.md` — uma spec por story do escopo (descrição + CTs BDD).
- `skills/<slug>.md` — uma lição por defeito com causa raiz registrada,
  estruturada como when/procedure/anti-pattern.

Mesma fonte de dados do context-pack (traceability + decisions + defects);
nenhum dado novo. Dois layouts: `agents-md` (padrão aberto) e `claude`
(skills em `.claude/skills/<slug>/SKILL.md`). White-label: nunca referencia
organização.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import frontmatter

from .metrics import traceability
from .workspace import slugify


def _body(root: Path, rel: str | None) -> str:
    if not rel:
        return ""
    path = root / rel
    if not path.exists():
        return ""
    return frontmatter.load(str(path)).content.strip()


def _scope_epics(conn, epic, story, squad) -> list[dict]:
    matrix = traceability(conn, epic, None, squad)
    epics = matrix["epics"]
    if story:
        epics = [
            {**e, "stories": [s for s in e["stories"] if s["id"] == story]}
            for e in epics
        ]
        epics = [e for e in epics if e["stories"]]
    return epics


def _first_paragraph(text: str) -> str:
    """Resumo curto: o primeiro parágrafo não-vazio, sem headings."""
    for block in text.split("\n\n"):
        cleaned = " ".join(
            ln.strip() for ln in block.splitlines() if not ln.strip().startswith("#")
        ).strip()
        if cleaned:
            return cleaned
    return ""


def _agents_md(root: Path, scope_label: str, decisions: list) -> str:
    lines = [
        "# AGENTS.md — contexto do escopo",
        "",
        f"Escopo: {scope_label}",
        "",
        "Pacote gerado pelo Arbites a partir dos artefatos de teste e decisão "
        "do projeto. Use-o como contexto de trabalho: as convenções abaixo são "
        "decisões arquiteturais ACEITAS; `specs/` traz os requisitos e casos de "
        "teste do escopo; `skills/` traz lições aprendidas de defeitos reais.",
        "",
        "## Convenções (decisões arquiteturais aceitas)",
        "",
    ]
    if not decisions:
        lines.append("_Nenhuma decisão aceita registrada para este escopo._")
    else:
        for d in decisions:
            summary = _first_paragraph(_body(root, d["path"]))
            lines.append(f"- **{d['id']} — {d['title']}**"
                         + (f": {summary}" if summary else ""))
    lines += [
        "",
        "## Glossário dos artefatos",
        "",
        "- **Story (ST-)**: requisito de usuário — o que deve ser validado.",
        "- **Caso de teste (CT-)**: roteiro (BDD) que valida uma story.",
        "- **Execução (EXEC-)**: uma rodada de CTs, com resultado por CT.",
        "- **Defeito (DF-)**: falha encontrada; com causa raiz registrada, "
        "vira uma skill em `skills/`.",
        "",
        "## Organização do pacote",
        "",
        "- `specs/` — uma spec por story do escopo (descrição + CTs BDD).",
        "- `skills/` — uma lição por defeito com causa raiz registrada "
        "(when/procedure/anti-pattern).",
        "",
    ]
    return "\n".join(lines)


def _spec_md(conn, root: Path, epic: dict, story: dict) -> str:
    lines = [
        f"# {story['id']} — {story['title']}",
        "",
        f"- Epic: {epic['id']} — {epic['title']}",
        f"- Status: {story['status']}",
        "",
    ]
    body = _body(root, _path_of(conn, "requirements", story["id"]))
    if body:
        lines += [body, ""]
    if story["testcases"]:
        lines += ["## Casos de teste", ""]
        for ct in story["testcases"]:
            lines.append(f"### {ct['id']} — {ct['title']} ({ct['status']})")
            ct_body = _body(root, _path_of(conn, "testcases", ct["id"]))
            if ct_body:
                lines += ["", ct_body, ""]
    return "\n".join(lines)


def _skill_md(slug: str, defect: sqlite3.Row) -> str:
    # lição ESTRUTURADA tem prioridade sobre causa/correção soltas (0095)
    keys = defect.keys()
    l_when = (defect["lesson_when"] if "lesson_when" in keys else None) or ""
    l_proc = (defect["lesson_procedure"] if "lesson_procedure" in keys else None) or ""
    l_anti = (defect["lesson_antipattern"] if "lesson_antipattern" in keys else None) or ""
    cause = (defect["root_cause"] or "").strip()
    fix = (defect["fix"] or "").strip()
    prevention = (defect["prevention"] or "").strip()
    when_body = l_when.strip() or cause
    proc_body = l_proc.strip() or fix
    anti_body = l_anti.strip() or prevention
    desc = f"Lição do defeito {defect['id']}: {defect['title']}."
    when = (f"Ao mexer em código relacionado a: {when_body}" if when_body
            else f"Contexto do defeito {defect['id']}.")
    lines = [
        "---",
        f"name: {slug}",
        f"description: {desc}",
        f"when: {when}",
        "---",
        "",
        f"# Skill — {slug}",
        "",
        f"Origem: defeito **{defect['id']} — {defect['title']}**.",
        "",
        "## When to use this skill",
        "",
        when_body or "Quando o contexto do defeito de origem se repetir.",
        "",
        "## Procedure",
        "",
        proc_body or "Corrija seguindo a resolução registrada no defeito de origem.",
        "",
        "## Anti-patterns",
        "",
        anti_body or "Evite reintroduzir a causa raiz descrita acima.",
        "",
    ]
    return "\n".join(lines)


def _path_of(conn, table: str, entity_id: str) -> str | None:
    row = conn.execute(
        f"SELECT path FROM {table} WHERE id = ?", (entity_id,)
    ).fetchone()
    return row["path"] if row else None


def build_pack(
    conn: sqlite3.Connection,
    root: Path,
    epic: str | None = None,
    story: str | None = None,
    squad: str | None = None,
    layout: str = "agents-md",
) -> dict:
    """Retorna `{files: {caminho: conteúdo}, counts}`. Chamador garante ao
    menos um filtro de escopo."""
    epics = _scope_epics(conn, epic, story, squad)

    scope_label = ", ".join(
        f"{k}={v}" for k, v in (("epic", epic), ("story", story), ("squad", squad)) if v
    )

    if squad:
        decisions = conn.execute(
            "SELECT id, title, status, path FROM decisions WHERE squad = ? ORDER BY id",
            (squad,),
        ).fetchall()
    else:
        decisions = conn.execute(
            "SELECT id, title, status, path FROM decisions"
            " WHERE status = 'accepted' ORDER BY id"
        ).fetchall()

    files: dict[str, str] = {"AGENTS.md": _agents_md(root, scope_label, decisions)}

    # specs por story + coleta de CT ids para achar defeitos do escopo
    ct_ids: list[str] = []
    spec_count = 0
    for e in epics:
        for s in e["stories"]:
            files[f"specs/{s['id']}-{slugify(s['title'])}.md"] = _spec_md(conn, root, e, s)
            spec_count += 1
            ct_ids += [ct["id"] for ct in s["testcases"]]

    # skills: uma por defeito COM causa raiz vinculado a um CT do escopo
    skill_count = 0
    if ct_ids:
        ph = ",".join("?" * len(ct_ids))
        defects = conn.execute(
            "SELECT id, title, root_cause, fix, prevention,"
            " lesson_when, lesson_procedure, lesson_antipattern FROM defects"
            f" WHERE testcase_id IN ({ph})"
            " AND ((root_cause IS NOT NULL AND root_cause != '')"
            "   OR (lesson_when IS NOT NULL AND lesson_when != ''))"
            " ORDER BY id",
            ct_ids,
        ).fetchall()
        for d in defects:
            slug = f"licao-{d['id'].lower()}-{slugify(d['title'])}"
            if layout == "claude":
                files[f".claude/skills/{slug}/SKILL.md"] = _skill_md(slug, d)
            else:
                files[f"skills/{slug}.md"] = _skill_md(slug, d)
            skill_count += 1

    return {
        "files": files,
        "counts": {
            "specs": spec_count,
            "skills": skill_count,
            "decisions": len(decisions),
        },
    }
