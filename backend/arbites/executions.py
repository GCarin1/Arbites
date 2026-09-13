"""Ciclo de execução manual — execution.json como fonte de verdade.

Três máquinas de estado independentes (ADR 0005):
  execution:  draft → in_progress → closed
  resultado:  pending → in_progress → passed|failed|blocked|retest (+ closed)
  documento CT: fora deste módulo (frontmatter do .md).

Toda mutação reescreve o execution.json e grava evento em history[].
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .workspace import Workspace

SCHEMA_VERSION = 1

RESULT_STATUSES = {"pending", "in_progress", "passed", "failed", "blocked", "retest"}
FINAL_STATUSES = {"passed", "failed", "blocked", "retest"}
KANBAN_COLUMNS = ["pending", "in_progress", "blocked", "failed", "retest", "passed"]


class ExecutionError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# O ciclo é a execution (ADR 0013): o período mora aqui, não numa entidade
# Sprint. Vocabulário do produto para os estados que já existem no disco.
CYCLE_LABELS = {"draft": "planejado", "in_progress": "em andamento",
                "closed": "fechado"}


def _parse_date(value: str | None, field: str) -> str | None:
    """Aceita `YYYY-MM-DD` ou vazio. Data inválida é recusada na entrada, e
    não descoberta depois por quem for ordenar ciclos por prazo."""
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ExecutionError(
            "invalid_date", f"{field} precisa ser uma data ISO (YYYY-MM-DD)"
        ) from None


def exec_dir(ws: Workspace, exec_id: str, created_at: str) -> Path:
    year = created_at[:4]
    return ws.root / "executions" / year / exec_id


def exec_path_of(ws: Workspace, exec_id: str) -> Path:
    """Localiza o execution.json de um id varrendo executions/ (fonte: disco)."""
    base = ws.root / "executions"
    if base.exists():
        for candidate in base.glob(f"*/{exec_id}/execution.json"):
            return candidate
    raise ExecutionError("not_found", f"{exec_id} não encontrada", 404)


def load(ws: Workspace, exec_id: str) -> dict[str, Any]:
    path = exec_path_of(ws, exec_id)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(ws: Workspace, execution: dict[str, Any]) -> Path:
    path = exec_dir(ws, execution["id"], execution["created_at"]) / "execution.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(execution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def create(
    ws: Workspace,
    name: str,
    owner: str,
    sprint: str | None,
    environment: str | None,
    testcases: list[dict[str, Any]],
    origin: str = "manual",
    squad: str | None = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
) -> dict[str, Any]:
    """Cria a execution com snapshot dos steps de cada CT (histórico fiel)."""
    exec_id = ws.next_id("execution")
    now = _now()
    results = []
    for tc in testcases:
        results.append(
            {
                "testcase_id": tc["id"],
                "status": "pending",
                "column": "pending",
                "assignee": None,
                "executed_by": None,
                "executed_at": None,
                "duration_seconds": None,
                "steps": [
                    {"index": i + 1, "text": text, "status": "pending"}
                    for i, text in enumerate(tc.get("steps") or [])
                ],
                "evidences": [],
                "defects": [],
                "comment": None,
                "error": None,
            }
        )
    execution = {
        "schema_version": SCHEMA_VERSION,
        "id": exec_id,
        "name": name,
        "owner": owner,
        "sprint": sprint,
        "environment": environment,
        "squad": (squad.strip() or None) if squad else None,
        "origin": origin,
        "created_at": now,
        "starts_on": None,
        "ends_on": None,
        "closed_at": None,
        "status": "draft",
        "ci": None,
        "results": results,
        "history": [{"at": now, "who": owner, "event": "created"}],
    }
    set_period(execution, starts_on, ends_on)
    save(ws, execution)
    return execution


def _find_result(execution: dict[str, Any], testcase_id: str) -> dict[str, Any]:
    for result in execution["results"]:
        if result["testcase_id"] == testcase_id:
            return result
    raise ExecutionError(
        "not_found", f"{testcase_id} não está na {execution['id']}", 404
    )


def _guard_open(execution: dict[str, Any]) -> None:
    if execution["status"] == "closed":
        raise ExecutionError(
            "execution_closed",
            f"{execution['id']} está fechada; resultados são imutáveis",
            409,
        )


def _activate(execution: dict[str, Any]) -> None:
    if execution["status"] == "draft":
        execution["status"] = "in_progress"


def set_result_status(
    execution: dict[str, Any],
    testcase_id: str,
    status: str,
    who: str,
    comment: str | None = None,
    column: str | None = None,
) -> dict[str, Any]:
    if status not in RESULT_STATUSES:
        raise ExecutionError("invalid_status", f"status inválido: {status}")
    _guard_open(execution)
    result = _find_result(execution, testcase_id)
    result["status"] = status
    result["column"] = column or status
    result["executed_by"] = who
    result["executed_at"] = _now()
    if comment is not None:
        result["comment"] = comment
    _activate(execution)
    execution["history"].append(
        {
            "at": _now(),
            "who": who,
            "event": "result",
            "testcase_id": testcase_id,
            "to": status,
        }
    )
    return result


def set_step_status(
    execution: dict[str, Any], testcase_id: str, step_index: int, status: str, who: str
) -> dict[str, Any]:
    if status not in {"pending", "passed", "failed", "blocked"}:
        raise ExecutionError("invalid_status", f"status de step inválido: {status}")
    _guard_open(execution)
    result = _find_result(execution, testcase_id)
    for step in result["steps"]:
        if step["index"] == step_index:
            step["status"] = status
            _activate(execution)
            execution["history"].append(
                {
                    "at": _now(),
                    "who": who,
                    "event": "step",
                    "testcase_id": testcase_id,
                    "step": step_index,
                    "to": status,
                }
            )
            return result
    raise ExecutionError(
        "not_found", f"step {step_index} não existe em {testcase_id}", 404
    )


def set_period(
    execution: dict[str, Any],
    starts_on: str | None,
    ends_on: str | None,
) -> dict[str, Any]:
    """Define o período do ciclo. Um ciclo que termina antes de começar é
    erro de digitação, não um estado que o produto precise representar."""
    start = _parse_date(starts_on, "starts_on")
    end = _parse_date(ends_on, "ends_on")
    if start and end and end < start:
        raise ExecutionError(
            "invalid_period", "ends_on não pode ser anterior a starts_on"
        )
    execution["starts_on"] = start
    execution["ends_on"] = end
    return execution


def set_assignee(
    execution: dict[str, Any], testcase_id: str, assignee: str | None, who: str
) -> dict[str, Any]:
    """Responsável por um caso DENTRO do ciclo — é o que permite dividir uma
    regressão entre duas ou mais pessoas sem duplicar a execution."""
    _guard_open(execution)
    result = _find_result(execution, testcase_id)
    value = (assignee or "").strip() or None
    result["assignee"] = value
    execution["history"].append(
        {
            "at": _now(),
            "who": who,
            "event": "assignee",
            "testcase_id": testcase_id,
            "to": value,
        }
    )
    return result


def progress(execution: dict[str, Any]) -> dict[str, Any]:
    """Cabeçalho de progresso do ciclo: contagem por COLUNA e total.

    Pela coluna, não pelo status cru: a ADR 0005 separou os dois de propósito
    e é a coluna que o time olha e move. Contar por status faria um caso
    arrastado para "Retest" aparecer na coluna Retest do quadro e como
    `passed` no progresso da mesma execution (change 0122).

    Derivado dos resultados a cada leitura — número guardado é número que
    diverge do que ele conta.
    """
    counts = {column: 0 for column in KANBAN_COLUMNS}
    for result in execution.get("results") or []:
        column = result.get("column") or result.get("status", "pending")
        counts[column] = counts.get(column, 0) + 1
    total = sum(counts.values())
    done = sum(counts.get(s, 0) for s in FINAL_STATUSES)
    return {
        "counts": counts,
        "total": total,
        "done": done,
        "percent": round(done * 100 / total) if total else 0,
    }


def add_evidence(
    ws: Workspace,
    execution: dict[str, Any],
    testcase_id: str,
    filename: str,
    content: bytes,
    mime: str | None,
    note: str | None,
    who: str,
) -> dict[str, Any]:
    _guard_open(execution)
    result = _find_result(execution, testcase_id)
    directory = (
        exec_dir(ws, execution["id"], execution["created_at"]) / "evidences" / testcase_id
    )
    directory.mkdir(parents=True, exist_ok=True)
    base = Path(Path(filename).name)
    dest = directory / base.name
    i = 1
    while dest.exists():
        dest = directory / f"{base.stem}-{i}{base.suffix}"
        i += 1
    dest.write_bytes(content)
    evidence = {
        "path": dest.relative_to(
            exec_dir(ws, execution["id"], execution["created_at"])
        ).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "mime": mime or "application/octet-stream",
        "captured_at": _now(),
        "note": note,
    }
    result["evidences"].append(evidence)
    _activate(execution)
    execution["history"].append(
        {
            "at": _now(),
            "who": who,
            "event": "evidence",
            "testcase_id": testcase_id,
            "path": evidence["path"],
        }
    )
    return evidence


def remove_evidence(
    ws: Workspace, execution: dict[str, Any], testcase_id: str, index: int, who: str
) -> None:
    _guard_open(execution)
    result = _find_result(execution, testcase_id)
    if not 0 <= index < len(result["evidences"]):
        raise ExecutionError("not_found", f"evidência {index} não existe", 404)
    evidence = result["evidences"].pop(index)
    file_path = exec_dir(ws, execution["id"], execution["created_at"]) / evidence["path"]
    if file_path.exists():
        ws.trash(file_path)
    execution["history"].append(
        {
            "at": _now(),
            "who": who,
            "event": "evidence_removed",
            "testcase_id": testcase_id,
            "path": evidence["path"],
        }
    )


def link_defect(
    execution: dict[str, Any], testcase_id: str, defect_id: str, who: str
) -> None:
    _guard_open(execution)
    result = _find_result(execution, testcase_id)
    if defect_id not in result["defects"]:
        result["defects"].append(defect_id)
        execution["history"].append(
            {
                "at": _now(),
                "who": who,
                "event": "defect",
                "testcase_id": testcase_id,
                "defect_id": defect_id,
            }
        )


def unlink_defect(
    execution: dict[str, Any], testcase_id: str, defect_id: str, who: str
) -> None:
    _guard_open(execution)
    result = _find_result(execution, testcase_id)
    if defect_id in result["defects"]:
        result["defects"].remove(defect_id)
        execution["history"].append(
            {
                "at": _now(),
                "who": who,
                "event": "defect_removed",
                "testcase_id": testcase_id,
                "defect_id": defect_id,
            }
        )


# -- diff entre executions (change 0088) --------------------------------------

# Ordenação de "qualidade" de um resultado, usada só para classificar a
# transição de um CT entre duas executions (melhor → maior).
_RESULT_RANK = {
    "passed": 4,
    "retest": 3,
    "blocked": 2,
    "failed": 1,
    "in_progress": 0,
    "pending": 0,
}


def diff_category(status_a: str, status_b: str) -> str:
    """Classifica a transição de um CT presente nas duas executions.

    - ``unchanged``: mesmo status nas duas.
    - ``regressed``: status_b é pior que status_a (ex.: passed→failed/blocked).
    - ``fixed``: status_b é melhor que status_a (ex.: failed→passed).
    """
    if status_a == status_b:
        return "unchanged"
    if _RESULT_RANK.get(status_b, 0) < _RESULT_RANK.get(status_a, 0):
        return "regressed"
    return "fixed"


def close(execution: dict[str, Any], who: str) -> None:
    if execution["status"] == "closed":
        raise ExecutionError("execution_closed", f"{execution['id']} já está fechada", 409)
    execution["status"] = "closed"
    execution["closed_at"] = _now()
    execution["history"].append({"at": _now(), "who": who, "event": "closed"})
