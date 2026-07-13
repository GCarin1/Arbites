"""Adapter do Cucumber JSON do Behave (risco §17: parser isolado).

Converte o JSON (`behave -f json`) num modelo neutro por CT. O run local
(M3) e a coleta de artifact do CI (M4) usam este mesmo módulo — executions
idênticas nos dois caminhos (ADR 0006). Fixtures de contrato versionadas
em backend/tests/fixtures/.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

_DEFAULT_CT_PREFIX = "CT"

_STATUS_MAP = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "blocked",
    "untested": "blocked",
    "undefined": "failed",
}


@dataclass
class ScenarioResult:
    testcase_id: str
    scenario_name: str
    status: str
    duration_seconds: float
    steps: list[dict] = field(default_factory=list)  # {index, text, status}
    error: str | None = None


class BehaveJsonError(Exception):
    pass


def parse_behave_json(
    content: bytes | str, ct_prefix: str = _DEFAULT_CT_PREFIX
) -> dict[str, ScenarioResult]:
    """Retorna {<PREFIXO>-XXXX: ScenarioResult} para cenários com tag do CT.

    `ct_prefix` vem de `id_prefixes.testcase` do workspace (default "CT" só
    para chamadas sem workspace, ex. testes unitários deste módulo) — um
    prefixo customizado não pode fazer os resultados do Behave sumirem
    silenciosamente na hora de casar com a execution.
    """
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise BehaveJsonError(f"Cucumber JSON inválido: {exc}") from exc
    if not isinstance(data, list):
        raise BehaveJsonError("Cucumber JSON inválido: raiz não é lista")

    ct_re = re.compile(rf"^@?({re.escape(ct_prefix)}-\d+)$")
    results: dict[str, ScenarioResult] = {}
    for feature in data:
        for element in feature.get("elements") or []:
            if element.get("type") not in ("scenario", None):
                continue
            ct_id = None
            for tag in element.get("tags") or []:
                m = ct_re.match(str(tag))
                if m:
                    ct_id = m.group(1)
                    break
            if not ct_id:
                continue

            steps = []
            duration = 0.0
            worst = "passed"
            error = None
            for i, step in enumerate(element.get("steps") or [], 1):
                result = step.get("result") or {}
                raw_status = result.get("status", "untested")
                status = _STATUS_MAP.get(raw_status, "blocked")
                duration += float(result.get("duration") or 0.0)
                if raw_status == "failed" and error is None:
                    error_lines = result.get("error_message") or []
                    if isinstance(error_lines, list):
                        error = "\n".join(str(line) for line in error_lines)
                    else:
                        error = str(error_lines)
                if status == "failed":
                    worst = "failed"
                elif status == "blocked" and worst == "passed":
                    worst = "blocked"
                steps.append(
                    {
                        "index": i,
                        "text": f"{step.get('keyword', '').strip()} "
                                f"{step.get('name', '')}".strip(),
                        "status": "pending" if raw_status in ("untested", "skipped")
                        else _STATUS_MAP.get(raw_status, "pending"),
                    }
                )

            # o status do elemento (quando presente) tem precedência
            element_status = element.get("status")
            status_final = _STATUS_MAP.get(element_status, worst) if element_status else worst
            results[ct_id] = ScenarioResult(
                testcase_id=ct_id,
                scenario_name=element.get("name", ""),
                status=status_final,
                duration_seconds=round(duration, 3),
                steps=steps,
                error=error,
            )
    return results
