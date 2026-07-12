"""Context Pack — bundle Markdown único (RAG-ready) com requisitos, casos de
teste, defeitos e decisões relevantes a um escopo (epic/story/squad), para
agentes de IA externos (Cursor, Claude Code, Codex, Roo Code, Aider, etc.)
que precisam de contexto do projeto sob teste sem acesso direto ao
workspace. Reaproveita `traceability()` como esqueleto e enriquece cada nó
com o corpo (Markdown) do artefato lido do disco.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import frontmatter

from .metrics import traceability


def _body(root: Path, rel: str | None) -> str:
    if not rel:
        return ""
    path = root / rel
    if not path.exists():
        return ""
    return frontmatter.load(str(path)).content.strip()


def build(
    conn: sqlite3.Connection,
    root: Path,
    epic: str | None = None,
    story: str | None = None,
    squad: str | None = None,
) -> str:
    """Monta o bundle Markdown. Chamador garante ao menos um filtro de escopo."""
    matrix = traceability(conn, epic, None, squad)
    epics = matrix["epics"]
    if story:
        epics = [
            {**e, "stories": [s for s in e["stories"] if s["id"] == story]}
            for e in epics
        ]
        epics = [e for e in epics if e["stories"]]

    scope_bits = [
        f"{label}={value}"
        for label, value in (("epic", epic), ("story", story), ("squad", squad))
        if value
    ]
    lines = ["# Context Pack", "", f"Escopo: {', '.join(scope_bits)}", ""]

    if not epics:
        lines.append("_Nenhum requisito encontrado para este escopo._")
        return "\n".join(lines)

    for e in epics:
        e_path = conn.execute(
            "SELECT path FROM requirements WHERE id = ?", (e["id"],)
        ).fetchone()
        lines.append(f"## Epic {e['id']} — {e['title']} ({e['status']})")
        e_body = _body(root, e_path["path"] if e_path else None)
        if e_body:
            lines += ["", e_body, ""]

        for s in e["stories"]:
            s_path = conn.execute(
                "SELECT path FROM requirements WHERE id = ?", (s["id"],)
            ).fetchone()
            lines.append(f"### Story {s['id']} — {s['title']} ({s['status']})")
            s_body = _body(root, s_path["path"] if s_path else None)
            if s_body:
                lines += ["", s_body, ""]

            if s["testcases"]:
                lines += ["**Casos de teste:**", ""]
                for ct in s["testcases"]:
                    ct_path = conn.execute(
                        "SELECT path FROM testcases WHERE id = ?", (ct["id"],)
                    ).fetchone()
                    lines.append(f"#### {ct['id']} — {ct['title']} ({ct['status']})")
                    ct_body = _body(root, ct_path["path"] if ct_path else None)
                    if ct_body:
                        lines += ["", ct_body, ""]

            if s["defects"]:
                lines += ["**Defeitos:**", ""]
                for d in s["defects"]:
                    d_row = conn.execute(
                        "SELECT path, root_cause, fix, prevention FROM defects"
                        " WHERE id = ?",
                        (d["id"],),
                    ).fetchone()
                    severity = d["severity"] or "sem severidade"
                    lines.append(f'- **{d["id"]}** "{d["title"]}" ({d["status"]}, {severity})')
                    if d_row and d_row["root_cause"]:
                        lines.append(f"  - causa raiz: {d_row['root_cause']}")
                    if d_row and d_row["fix"]:
                        lines.append(f"  - correção: {d_row['fix']}")
                    if d_row and d_row["prevention"]:
                        lines.append(f"  - prevenção: {d_row['prevention']}")
                lines.append("")

    if squad:
        decisions = conn.execute(
            "SELECT id, title, status, path FROM decisions WHERE squad = ? ORDER BY id",
            (squad,),
        ).fetchall()
        if decisions:
            lines += ["## Decisões arquiteturais", ""]
            for dec in decisions:
                lines.append(f"### {dec['id']} — {dec['title']} ({dec['status']})")
                dec_body = _body(root, dec["path"])
                if dec_body:
                    lines += ["", dec_body, ""]

    return "\n".join(lines)
