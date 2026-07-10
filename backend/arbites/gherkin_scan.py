"""Scan de feature files dos automation targets (read-only, ADR 0003).

Usa o pacote oficial `gherkin`, que resolve `# language:` nativamente.
Monta o mapa `@CT-XXXX → (feature_file, scenario_name, line)` na tabela
`scenarios` e popula os warnings de integridade do reindex:
  - `orphan_scenario`   — tag @CT sem CT correspondente no índice
  - `broken_automation` — CT automated/hybrid sem cenário com a tag
  - `duplicate_scenario_tag` — mesma tag em dois cenários (erro)
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gherkin.parser import Parser

_CT_TAG_RE = re.compile(r"^@(CT-\d+)$")
_SCAN_WARNING_CODES = ("orphan_scenario", "broken_automation",
                       "duplicate_scenario_tag", "unparseable_feature")


def scan_target(
    ws_root_unused: Any, conn: sqlite3.Connection, target: dict[str, Any]
) -> dict[str, Any]:
    """Re-escaneia um target; substitui as linhas dele em `scenarios`."""
    name = str(target.get("name"))
    local_path = Path(str(target.get("local_path", "")))
    glob = str(target.get("features_glob", "features/**/*.feature"))

    conn.execute("DELETE FROM scenarios WHERE target = ?", (name,))
    placeholders = ",".join("?" for _ in _SCAN_WARNING_CODES)
    conn.execute(
        f"DELETE FROM warnings WHERE code IN ({placeholders})"
        " AND source_path LIKE ?",
        (*_SCAN_WARNING_CODES, f"{name}:%"),
    )

    def warn(code: str, source: str, message: str) -> None:
        conn.execute(
            "INSERT INTO warnings(source_path, code, message, created_at)"
            " VALUES (?,?,?,?)",
            (f"{name}:{source}", code, message,
             datetime.now(timezone.utc).isoformat()),
        )

    if not local_path.is_dir():
        warn("unparseable_feature", str(local_path),
             f"local_path do target '{name}' não existe: {local_path}")
        conn.commit()
        return {"target": name, "scenarios": 0, "features": 0}

    parser = Parser()
    seen_tags: dict[str, str] = {}
    scenario_count = 0
    feature_count = 0

    for feature_path in sorted(local_path.glob(glob)):
        rel = feature_path.relative_to(local_path).as_posix()
        try:
            doc = parser.parse(feature_path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # erro de sintaxe Gherkin → warning, não crash
            warn("unparseable_feature", rel, f"{rel}: {exc}")
            continue
        feature = doc.get("feature")
        if not feature:
            continue
        feature_count += 1
        language = feature.get("language", "en")
        for child in feature.get("children", []):
            scenario = child.get("scenario")
            if not scenario:
                continue
            scenario_count += 1
            for tag in scenario.get("tags", []):
                tag_name = tag.get("name", "")
                if not _CT_TAG_RE.match(tag_name):
                    continue
                where = f"{rel}:{scenario['location']['line']}"
                if tag_name in seen_tags:
                    for place in (seen_tags[tag_name], where):
                        warn(
                            "duplicate_scenario_tag", place,
                            f"tag {tag_name} duplicada em {seen_tags[tag_name]}"
                            f" e {where}",
                        )
                    continue
                seen_tags[tag_name] = where
                conn.execute(
                    "INSERT OR REPLACE INTO scenarios"
                    "(target, tag, feature_path, scenario_name, line, language)"
                    " VALUES (?,?,?,?,?,?)",
                    (name, tag_name, rel, scenario.get("name", ""),
                     scenario["location"]["line"], language),
                )

    # cruzamentos com o índice de CTs
    for tag_name, where in seen_tags.items():
        ct_id = tag_name.lstrip("@")
        if not conn.execute(
            "SELECT 1 FROM testcases WHERE id = ?", (ct_id,)
        ).fetchone():
            warn("orphan_scenario", where,
                 f"cenário órfão: tag {tag_name} sem CT correspondente")
    for row in conn.execute(
        "SELECT id, scenario_tag FROM testcases"
        " WHERE type IN ('automated','hybrid') AND automation_target = ?",
        (name,),
    ).fetchall():
        expected = row["scenario_tag"] or f"@{row['id']}"
        if expected not in seen_tags:
            warn("broken_automation", row["id"],
                 f"automação quebrada: {row['id']} espera cenário com tag"
                 f" {expected} no target '{name}'")

    conn.commit()
    return {"target": name, "scenarios": scenario_count, "features": feature_count}


def list_feature_files(
    local_path: Path, glob: str = "features/**/*.feature"
) -> list[dict[str, Any]]:
    """Lista .feature sob `local_path` sem tocar no índice (scan avulso).

    Usado pelo formulário de target ANTES de ele existir/ser salvo — mostra
    ao usuário o que o glob resolve de verdade, para ele escolher em vez de
    digitar um path/glob às cegas.
    """
    if not local_path.is_dir():
        raise FileNotFoundError(f"pasta não encontrada: {local_path}")
    parser = Parser()
    out: list[dict[str, Any]] = []
    for feature_path in sorted(local_path.glob(glob)):
        rel = feature_path.relative_to(local_path).as_posix()
        scenarios = 0
        parseable = True
        try:
            doc = parser.parse(feature_path.read_text(encoding="utf-8-sig"))
            feature = doc.get("feature")
            if feature:
                scenarios = sum(
                    1 for child in feature.get("children", []) if child.get("scenario")
                )
        except Exception:
            parseable = False
        out.append({"path": rel, "scenarios": scenarios, "parseable": parseable})
    return out


def scan_all_targets(ws, conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Chamado pelo reindex completo: escaneia todos os targets da config."""
    results = []
    for target in ws.config().get("automation_targets") or []:
        if target.get("local_path"):
            results.append(scan_target(ws, conn, target))
    return results
