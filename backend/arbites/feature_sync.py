"""Sincronização .feature ↔ CT por NOME de cenário (mudança 0075).

O repositório de automação é read-only (ADR 0003): o Arbites nunca escreve
tag lá. O vínculo alternativo à tag é `automation.feature_path` +
`scenario_name` no frontmatter do CT. Vínculo por nome é frágil por
natureza (rename quebra) — a mitigação é esta sync explícita e
re-executável, que classifica cada cenário do repositório:

  - `linked_tag`  — cenário tagueado @CT- (vínculo forte, fora da sync)
  - `linked`      — vinculado por nome, steps iguais aos do CT
  - `modified`    — vinculado por nome, steps divergiram do body do CT
  - `new`         — sem vínculo nenhum (candidato a criar CT)

e os vínculos quebrados (CT aponta para cenário que sumiu/renomeou). Quem
decide o que criar/atualizar/re-vincular é o usuário, no modal — nunca
auto-fix (skill vinculo-por-nome-exige-sync-explicita).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from gherkin.parser import Parser

from .gherkin_scan import DEFAULT_FEATURES_GLOB
from .parser import parse_markdown
from .workspace import Workspace


def _norm_steps(steps: list[str]) -> list[str]:
    return [re.sub(r"\s+", " ", s).strip() for s in steps if s.strip()]


def scan_feature_files(
    local_path: Path, glob: str = DEFAULT_FEATURES_GLOB
) -> list[dict[str, Any]]:
    """Estrutura completa dos .feature (nome, cenários, steps verbatim)."""
    parser = Parser()
    out: list[dict[str, Any]] = []
    for fp in sorted(local_path.glob(glob)):
        rel = fp.relative_to(local_path).as_posix()
        try:
            doc = parser.parse(fp.read_text(encoding="utf-8-sig"))
        except Exception:
            continue  # sintaxe inválida aparece nos warnings do scan normal
        feature = doc.get("feature")
        if not feature:
            continue
        scenarios = []
        for child in feature.get("children", []):
            sc = child.get("scenario")
            if not sc:
                continue
            steps = [
                f"{step.get('keyword', '').strip()} {step.get('text', '')}".strip()
                for step in sc.get("steps", [])
            ]
            scenarios.append({
                "name": sc.get("name", ""),
                "line": sc["location"]["line"],
                "tags": [t.get("name", "") for t in sc.get("tags", [])],
                "steps": steps,
            })
        out.append({
            "path": rel,
            "feature_name": feature.get("name", ""),
            "language": feature.get("language", "en"),
            "scenarios": scenarios,
        })
    return out


def scenario_body(feature_name: str, scenario: dict[str, Any], language: str) -> str:
    """Body BDD verbatim do CT criado a partir de um cenário."""
    header = "# language: %s\n" % language if language and language != "en" else ""
    kw_feature = "Funcionalidade" if language == "pt" else "Feature"
    kw_scenario = "Cenário" if language == "pt" else "Scenario"
    lines = [f"{header}{kw_feature}: {feature_name}", ""]
    lines.append(f"  {kw_scenario}: {scenario['name']}")
    for step in scenario["steps"]:
        lines.append(f"    {step}")
    return "\n".join(lines) + "\n"


def sync_status(
    ws: Workspace, conn: sqlite3.Connection, target: dict[str, Any],
    ct_tag_re: re.Pattern[str],
) -> dict[str, Any]:
    """Compara o estado atual dos .feature com os CTs vinculados do target."""
    name = str(target.get("name"))
    local_path = Path(str(target.get("local_path", "")))
    glob = str(target.get("features_glob") or DEFAULT_FEATURES_GLOB)
    if not local_path.is_dir():
        return {"target": name, "features": [], "broken": [],
                "error": f"local_path não encontrado: {local_path}"}

    # CTs vinculados por nome no target: (feature_path, scenario_name) → row
    linked = {
        (r["feature_path"], r["scenario_name"]): r
        for r in conn.execute(
            "SELECT id, path, feature_path, scenario_name FROM testcases"
            " WHERE automation_target = ? AND scenario_name IS NOT NULL"
            " AND feature_path IS NOT NULL",
            (name,),
        )
    }
    seen: set[tuple[str, str]] = set()
    features_out = []
    for feat in scan_feature_files(local_path, glob):
        scenarios_out = []
        for sc in feat["scenarios"]:
            key = (feat["path"], sc["name"])
            seen.add(key)
            has_ct_tag = any(ct_tag_re.match(t) for t in sc["tags"])
            if has_ct_tag:
                status, ct_id = "linked_tag", None
            elif key in linked:
                row = linked[key]
                ct_id = row["id"]
                # steps do CT (baseline do diff) vivem no próprio body
                doc = parse_markdown(ws.root / row["path"])
                if _norm_steps(doc.steps) == _norm_steps(sc["steps"]):
                    status = "linked"
                else:
                    status = "modified"
            else:
                status, ct_id = "new", None
            scenarios_out.append({
                "name": sc["name"], "line": sc["line"], "status": status,
                "ct_id": ct_id, "steps": sc["steps"],
            })
        features_out.append({
            "path": feat["path"], "feature_name": feat["feature_name"],
            "language": feat["language"], "scenarios": scenarios_out,
        })

    broken = [
        {"ct_id": r["id"], "feature_path": fp, "scenario_name": sn}
        for (fp, sn), r in linked.items() if (fp, sn) not in seen
    ]
    return {"target": name, "features": features_out, "broken": broken,
            "error": None}
