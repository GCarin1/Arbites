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


def _last_result(conn: sqlite3.Connection, ct_id: str) -> str:
    """Último status de execução do CT (mais recente), ou "" se nunca rodou."""
    row = conn.execute(
        "SELECT status, executed_at FROM results WHERE testcase_id = ?"
        " ORDER BY executed_at DESC, execution_id DESC LIMIT 1",
        (ct_id,),
    ).fetchone()
    if not row or not row["status"]:
        return ""
    when = f" em {row['executed_at']}" if row["executed_at"] else ""
    return f"{row['status']}{when}"


def build(
    conn: sqlite3.Connection,
    root: Path,
    epic: str | None = None,
    story: str | None = None,
    squad: str | None = None,
    *,
    include_testcases: bool = True,
    include_defects: bool = True,
    include_decisions: bool = True,
    include_last_result: bool = False,
) -> dict:
    """Monta o bundle Markdown. Chamador garante ao menos um filtro de escopo.

    Retorna `{"markdown", "counts", "bytes"}` — `counts` conta os requisitos,
    CTs, defeitos e decisões efetivamente incluídos (respeitando os toggles),
    para o preview da UI."""
    matrix = traceability(conn, epic, None, squad)
    epics = matrix["epics"]
    if story:
        epics = [
            {**e, "stories": [s for s in e["stories"] if s["id"] == story]}
            for e in epics
        ]
        epics = [e for e in epics if e["stories"]]

    counts = {"requirements": 0, "testcases": 0, "defects": 0, "decisions": 0}

    scope_bits = [
        f"{label}={value}"
        for label, value in (("epic", epic), ("story", story), ("squad", squad))
        if value
    ]
    lines = ["# Context Pack", "", f"Escopo: {', '.join(scope_bits)}", ""]

    if not epics:
        lines.append("_Nenhum requisito encontrado para este escopo._")
        markdown = "\n".join(lines)
        return {"markdown": markdown, "counts": counts,
                "bytes": len(markdown.encode("utf-8"))}

    for e in epics:
        e_path = conn.execute(
            "SELECT path FROM requirements WHERE id = ?", (e["id"],)
        ).fetchone()
        lines.append(f"## Epic {e['id']} — {e['title']} ({e['status']})")
        counts["requirements"] += 1
        e_body = _body(root, e_path["path"] if e_path else None)
        if e_body:
            lines += ["", e_body, ""]

        for s in e["stories"]:
            s_path = conn.execute(
                "SELECT path FROM requirements WHERE id = ?", (s["id"],)
            ).fetchone()
            lines.append(f"### Story {s['id']} — {s['title']} ({s['status']})")
            counts["requirements"] += 1
            s_body = _body(root, s_path["path"] if s_path else None)
            if s_body:
                lines += ["", s_body, ""]

            if include_testcases and s["testcases"]:
                lines += ["**Casos de teste:**", ""]
                for ct in s["testcases"]:
                    ct_path = conn.execute(
                        "SELECT path FROM testcases WHERE id = ?", (ct["id"],)
                    ).fetchone()
                    lines.append(f"#### {ct['id']} — {ct['title']} ({ct['status']})")
                    counts["testcases"] += 1
                    if include_last_result:
                        last = _last_result(conn, ct["id"])
                        lines.append(
                            f"_Último resultado: {last}_" if last
                            else "_Último resultado: nunca executado_"
                        )
                    ct_body = _body(root, ct_path["path"] if ct_path else None)
                    if ct_body:
                        lines += ["", ct_body, ""]

            if include_defects and s["defects"]:
                lines += ["**Defeitos:**", ""]
                for d in s["defects"]:
                    d_row = conn.execute(
                        "SELECT path, root_cause, fix, prevention FROM defects"
                        " WHERE id = ?",
                        (d["id"],),
                    ).fetchone()
                    severity = d["severity"] or "sem severidade"
                    lines.append(f'- **{d["id"]}** "{d["title"]}" ({d["status"]}, {severity})')
                    counts["defects"] += 1
                    if d_row and d_row["root_cause"]:
                        lines.append(f"  - causa raiz: {d_row['root_cause']}")
                    if d_row and d_row["fix"]:
                        lines.append(f"  - correção: {d_row['fix']}")
                    if d_row and d_row["prevention"]:
                        lines.append(f"  - prevenção: {d_row['prevention']}")
                lines.append("")

    # Decisões arquiteturais: em QUALQUER escopo (não só squad) — as do squad
    # filtrado quando há squad, senão as ADRs aceitas do projeto (contexto
    # arquitetural transversal para o agente externo).
    if include_decisions:
        if squad:
            decisions = conn.execute(
                "SELECT id, title, status, path FROM decisions WHERE squad = ?"
                " ORDER BY id",
                (squad,),
            ).fetchall()
        else:
            decisions = conn.execute(
                "SELECT id, title, status, path FROM decisions"
                " WHERE status = 'accepted' ORDER BY id"
            ).fetchall()
        if decisions:
            lines += ["## Decisões arquiteturais", ""]
            for dec in decisions:
                lines.append(f"### {dec['id']} — {dec['title']} ({dec['status']})")
                counts["decisions"] += 1
                dec_body = _body(root, dec["path"])
                if dec_body:
                    lines += ["", dec_body, ""]

    markdown = "\n".join(lines)
    return {"markdown": markdown, "counts": counts,
            "bytes": len(markdown.encode("utf-8"))}
