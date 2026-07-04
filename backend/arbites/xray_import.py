"""Migração Xray (M2) — adapter de parsing + preview/confirm idempotente.

Formato suportado: XML de export do Jira (RSS) com os custom fields do
Xray — "Manual Test Steps" (JSON embutido), prioridade, labels e
issuelinks para a story testada. O parser converte tudo para o modelo
neutro `XrayTest`; o resto do fluxo não conhece XML. Se o export real
divergir, só este módulo muda (testes de contrato em
backend/tests/fixtures/).

Regras (spec xray-migration): preview nunca escreve; confirm é
idempotente por `external_key`; ferramenta de migração pontual, não
integração (ADR 0007).
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

from .workspace import Workspace

_PRIORITY_MAP = {
    "highest": "critical",
    "blocker": "critical",
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "lowest": "low",
    "minor": "low",
    "trivial": "low",
}

_TAG_RE = re.compile(r"<[^>]+>")


class XrayImportError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class XrayStep:
    action: str
    data: str = ""
    expected: str = ""


@dataclass
class XrayTest:
    key: str
    title: str
    priority: str = "medium"
    labels: list[str] = field(default_factory=list)
    steps: list[XrayStep] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    story_key: str | None = None
    unmapped: list[str] = field(default_factory=list)  # campos ignorados, p/ preview


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text or "").strip()


def parse_xray_xml(content: bytes) -> list[XrayTest]:
    """Parseia o XML de export para o modelo neutro."""
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise XrayImportError("invalid_xml", f"XML inválido: {exc}") from exc

    items = root.findall(".//item")
    if not items:
        raise XrayImportError("no_tests", "nenhum <item> encontrado no XML")

    tests: list[XrayTest] = []
    for item in items:
        key = (item.findtext("key") or "").strip()
        title = _strip_html(item.findtext("summary") or item.findtext("title") or key)
        if not key:
            continue
        test = XrayTest(key=key, title=title)
        priority = (item.findtext("priority") or "").strip().lower()
        test.priority = _PRIORITY_MAP.get(priority, "medium")
        test.labels = [
            (label.text or "").strip()
            for label in item.findall(".//labels/label")
            if (label.text or "").strip()
        ]
        for link in item.findall(".//issuelinks//issuelink/issuekey"):
            if link.text:
                test.story_key = link.text.strip()
                break

        for custom in item.findall(".//customfields/customfield"):
            name = (custom.findtext("customfieldname") or "").strip().lower()
            values = [
                v.text or "" for v in custom.findall(".//customfieldvalues/customfieldvalue")
            ]
            raw = "\n".join(values).strip()
            if not raw:
                continue
            if name == "manual test steps":
                test.steps = _parse_steps_json(raw, test)
            elif name in ("pre-condition", "preconditions", "pre-conditions"):
                test.prerequisites = [
                    _strip_html(line) for line in raw.splitlines() if _strip_html(line)
                ]
            else:
                test.unmapped.append(custom.findtext("customfieldname") or name)
        tests.append(test)
    return tests


def _parse_steps_json(raw: str, test: XrayTest) -> list[XrayStep]:
    """Steps do Xray vêm como JSON: [{index, fields: {Action, Data, Expected Result}}]."""
    try:
        data = json.loads(raw)
    except ValueError:
        test.unmapped.append("Manual Test Steps (JSON ilegível)")
        return []
    steps = []
    for entry in sorted(data, key=lambda e: e.get("index", 0)):
        fields = entry.get("fields") or {}
        steps.append(
            XrayStep(
                action=_strip_html(str(fields.get("Action", ""))),
                data=_strip_html(str(fields.get("Data", ""))),
                expected=_strip_html(str(fields.get("Expected Result", ""))),
            )
        )
    return [s for s in steps if s.action]


# ---------------------------------------------------------------------------
# Preview / confirm


def preview(conn: sqlite3.Connection, tests: list[XrayTest]) -> dict[str, Any]:
    """Tabela do que será criado — o disco fica intocado."""
    rows = []
    story_keys: dict[str, bool] = {}
    for test in tests:
        existing = conn.execute(
            "SELECT id FROM testcases WHERE external_key = ?", (test.key,)
        ).fetchone()
        if test.story_key is not None and test.story_key not in story_keys:
            story_keys[test.story_key] = bool(
                conn.execute(
                    "SELECT 1 FROM requirements WHERE external_key = ?",
                    (test.story_key,),
                ).fetchone()
            )
        rows.append(
            {
                "external_key": test.key,
                "title": test.title,
                "priority": test.priority,
                "labels": test.labels,
                "steps": len(test.steps),
                "story_key": test.story_key,
                "action": "skip (já migrado)" if existing else "create",
                "existing_id": existing["id"] if existing else None,
                "unmapped": test.unmapped,
            }
        )
    return {
        "tests": rows,
        "stories": [
            {"external_key": key, "exists_locally": exists}
            for key, exists in sorted(story_keys.items())
        ],
    }


def body_from_test(test: XrayTest) -> str:
    lines = ["## Objetivo", "", f"Migrado do Xray ({test.key}).", ""]
    lines += ["## Pré-condições", ""]
    lines += [f"- {p}" for p in test.prerequisites] or ["-"]
    lines += ["", "## Passos", ""]
    if test.steps:
        for i, step in enumerate(test.steps, 1):
            suffix = f" (dados: {step.data})" if step.data else ""
            lines.append(f"{i}. {step.action}{suffix}")
    else:
        lines.append("1. (sem steps no export)")
    lines += ["", "## Resultado esperado", ""]
    if any(s.expected for s in test.steps):
        for i, step in enumerate(test.steps, 1):
            lines.append(f"{i}. {step.expected or '—'}")
    else:
        lines.append("Conforme comportamento validado no Xray.")
    lines.append("")
    return "\n".join(lines)


def confirm(
    ws: Workspace,
    conn: sqlite3.Connection,
    tests: list[XrayTest],
    folder: str,
    create_stories: list[str],
    write_doc,
    reindex,
) -> dict[str, Any]:
    """Aplica a migração. Idempotente: external_key já migrado é pulado."""
    from .workspace import slugify

    created_stories: dict[str, str] = {}
    for story_key in create_stories:
        row = conn.execute(
            "SELECT id FROM requirements WHERE external_key = ?", (story_key,)
        ).fetchone()
        if row:
            created_stories[story_key] = row["id"]
            continue
        story_id = ws.next_id("story")
        meta = {
            "id": story_id,
            "kind": "story",
            "title": f"Story {story_key} (migrada do Xray)",
            "status": "active",
            "external_key": story_key,
            "tags": ["xray-import"],
        }
        path = ws.root / "requirements" / f"{story_id}-{slugify(story_key)}.md"
        write_doc(path, meta, f"## Resumo\n\nEspelho local da issue {story_key}.\n")
        reindex(path)
        created_stories[story_key] = story_id

    def local_story_id(story_key: str | None) -> str | None:
        if not story_key:
            return None
        if story_key in created_stories:
            return created_stories[story_key]
        row = conn.execute(
            "SELECT id FROM requirements WHERE external_key = ?", (story_key,)
        ).fetchone()
        return row["id"] if row else None

    folder = folder.strip("/").replace("\\", "/")
    target_dir = ws.root / "testcases" / folder if folder else ws.root / "testcases"
    created, skipped = [], []
    for test in tests:
        existing = conn.execute(
            "SELECT id FROM testcases WHERE external_key = ?", (test.key,)
        ).fetchone()
        if existing:
            skipped.append({"external_key": test.key, "id": existing["id"]})
            continue
        ct_id = ws.next_id("testcase")
        meta: dict[str, Any] = {
            "id": ct_id,
            "title": test.title,
            "type": "manual",
            "priority": test.priority,
            "status": "ready",
            "tags": test.labels,
            "story": local_story_id(test.story_key),
            "external_key": test.key,
        }
        path = target_dir / f"{ct_id}-{slugify(test.title)}.md"
        write_doc(path, meta, body_from_test(test))
        reindex(path)
        created.append({"external_key": test.key, "id": ct_id})
    return {
        "created": created,
        "skipped": skipped,
        "stories_created": created_stories,
    }
