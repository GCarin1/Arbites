"""Parser de artefatos Markdown — frontmatter YAML + âncoras de heading.

Regras (spec `indexing`): problemas de estrutura geram warning, não erro;
arquivos inválidos nunca são ignorados silenciosamente.

A extração de headings/steps é feita por varredura de linhas (não por AST):
o reindex completo precisa fechar em < 5 s para 2.000 CTs (SC8) e um parse
de AST por arquivo estoura esse orçamento.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:  # C loader quando disponível — ~10x mais rápido que o puro-Python
    _YamlLoader = yaml.CSafeLoader  # type: ignore[attr-defined]
except AttributeError:
    _YamlLoader = yaml.SafeLoader

REQUIRED_TC_HEADINGS = ["Passos", "Resultado esperado"]

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
_ORDERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
# BDD/Gherkin: steps são as linhas Given/When/Then/And/But (EN e PT-BR)
_GHERKIN_STEP_RE = re.compile(
    r"^\s*(Given|When|Then|And|But|Dado|Quando|Então|Entao|E|Mas)\s+(.+)$"
)
_GHERKIN_SCENARIO_RE = re.compile(r"^\s*(Scenario|Cenário|Cenario)\s*:", re.IGNORECASE)


@dataclass
class ParsedDoc:
    path: Path
    meta: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    headings: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    is_bdd: bool = False  # corpo em Gherkin (Scenario/Given/When/Then)
    warnings: list[tuple[str, str]] = field(default_factory=list)  # (code, message)

    @property
    def id(self) -> str | None:
        raw = self.meta.get("id")
        return str(raw) if raw is not None else None


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Separa o bloco YAML delimitado por '---' do corpo. (None = sem bloco)."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm = text[3:end]
    body = text[end + 4 :]
    if body.startswith("\r"):
        body = body[1:]
    if body.startswith("\n"):
        body = body[1:]
    return fm, body


def parse_markdown(path: Path) -> ParsedDoc:
    try:
        # utf-8-sig: tolera BOM gravado por editores externos (Notepad, PS)
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        doc = ParsedDoc(path=path)
        doc.warnings.append(("unreadable", f"{path.name}: {exc}"))
        return doc
    return parse_text(path, text)


def parse_text(path: Path, text: str) -> ParsedDoc:
    """Parseia a partir do texto já lido (o reindex completo lê em paralelo)."""
    doc = ParsedDoc(path=path)
    fm_text, body = split_frontmatter(text)
    doc.body = body
    if fm_text is None:
        doc.warnings.append(("invalid_frontmatter", f"{path.name}: frontmatter ausente"))
        _scan_body(doc)
        return doc
    try:
        meta = yaml.load(fm_text, Loader=_YamlLoader)
    except yaml.YAMLError as exc:
        doc.warnings.append(("invalid_frontmatter", f"{path.name}: {exc}"))
        _scan_body(doc)
        return doc
    if not isinstance(meta, dict):
        doc.warnings.append(
            ("invalid_frontmatter", f"{path.name}: frontmatter não é um mapeamento YAML")
        )
        _scan_body(doc)
        return doc
    doc.meta = meta
    if doc.id is None:
        doc.warnings.append(("missing_id", f"{path.name}: frontmatter sem campo 'id'"))
    _scan_body(doc)
    return doc


def check_testcase_headings(doc: ParsedDoc) -> None:
    """Âncoras obrigatórias p/ manual|hybrid; ausência = warning (spec).

    Corpo em BDD/Gherkin (Scenario + Given/When/Then) é o formato canônico
    novo e dispensa as âncoras markdown legadas.
    """
    tc_type = str(doc.meta.get("type", "manual"))
    if tc_type not in ("manual", "hybrid"):
        return
    if doc.is_bdd:
        return
    for heading in REQUIRED_TC_HEADINGS:
        if heading not in doc.headings:
            doc.warnings.append(
                (
                    "missing_heading",
                    f"{doc.path.name}: heading obrigatório '## {heading}' ausente "
                    f"para caso {tc_type} (use o formato BDD ou as âncoras markdown)",
                )
            )


def _scan_body(doc: ParsedDoc) -> None:
    """Uma passada pelas linhas: coleta headings, itens sob '## Passos' e,
    no formato BDD, os steps Given/When/Then (que viram os steps do CT)."""
    in_passos = False
    in_code = False
    gherkin_steps: list[str] = []
    has_scenario = False
    for line in doc.body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _HEADING_RE.match(line)
        if m:
            title = m.group(1).strip()
            doc.headings.append(title)
            in_passos = title == "Passos"
            continue
        if _GHERKIN_SCENARIO_RE.match(line):
            has_scenario = True
            continue
        g = _GHERKIN_STEP_RE.match(line)
        if g:
            gherkin_steps.append(stripped)
            continue
        if in_passos:
            item = _ORDERED_ITEM_RE.match(line)
            if item:
                doc.steps.append(item.group(1).strip())
    # BDD: com Scenario + steps Gherkin e sem '## Passos', os steps do CT
    # são as linhas Given/When/Then (na ordem)
    if has_scenario and gherkin_steps:
        doc.is_bdd = True
        if not doc.steps:
            doc.steps = gherkin_steps
