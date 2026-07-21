"""Runs locais de automação — subprocess direto na v1 (ADR 0004).

Fila FIFO com worker único por target (exclusão mútua + ordem), timeout
configurável (default 30 min) que marca pendentes como blocked, stdout em
buffer + broadcast SSE, `ARBITES_EVIDENCE_DIR` injetada no ambiente e
evidências dos hooks movidas para a execution e hasheadas. Os resultados
entram no mesmo execution.json do fluxo manual, via o adapter
`behave_json` (compartilhado com o M4).
"""

from __future__ import annotations

import asyncio
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import executions as exec_ops
from .behave_json import BehaveJsonError, parse_behave_json
from .indexer import clear_needs_rerun, reindex_file
from .workspace import Workspace

DEFAULT_TIMEOUT_MINUTES = 30.0


def load_env_file(path: Path) -> dict[str, str]:
    """Lê um `.env` estilo dotenv (KEY=VALUE) num dict, ignorando comentários e
    linhas em branco e removendo aspas do valor. Best-effort: um arquivo
    ilegível devolve `{}` (0099 — o Arbites se adapta ao projeto)."""
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return values
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if key.lower().startswith("export "):
            key = key[len("export "):].strip()
        if key:
            values[key] = value.strip().strip('"').strip("'")
    return values


def build_run_env(
    base_env: dict[str, str], local_path: Path, evidence_dir: Path
) -> dict[str, str]:
    """Ambiente do subprocess do run (0099): base + `.env` do projeto-alvo, com
    as chaves de controle do Arbites reafirmadas por último (o `.env` do
    projeto NUNCA sobrescreve `ARBITES_*`/`PYTHONIOENCODING`)."""
    env = dict(base_env)
    env.update(load_env_file(local_path / ".env"))
    env["ARBITES_EVIDENCE_DIR"] = str(evidence_dir)
    # o behave é Python: sem isto, no Windows o stdout sai no encoding do
    # console (cp1252) e a decodificação UTF-8 do pump vira mojibake
    # ("Cenário" → "Cen�rio") — quebrava o terminal ao vivo E o parse de
    # progresso (0076)
    env["PYTHONIOENCODING"] = "utf-8"
    return env

# Progresso ao vivo (mudança 0076) — parse best-effort do formato plain do
# behave, EN e PT. A fonte OFICIAL é sempre o Cucumber JSON do fim do run
# (_collect reconcilia incondicionalmente); o live só antecipa a UX.
_LIVE_SCENARIO_RE = re.compile(r"^\s*(?:Scenario|Cenário|Cenario)(?: Outline)?:\s*(.+?)\s*$")
_LIVE_STEP_RE = re.compile(
    r"^\s+(?:Given|When|Then|And|But|Dado|Quando|Então|Entao|E|Mas)\s+.*?"
    r"\s\.\.\.\s(passed|failed|undefined|skipped)\b"
)


class RunInfo:
    def __init__(self, exec_id: str, target: dict[str, Any], tags: list[str],
                 feature: str | None = None, features: list[str] | None = None,
                 live_map: dict[str, str] | None = None):
        self.exec_id = exec_id
        self.target = target
        self.tags = tags
        # 1..N caminhos relativos de .feature (posicionais do behave)
        self.features = list(features or ([feature] if feature else []))
        self.feature = self.features[0] if self.features else None  # compat
        # progresso ao vivo: nome do cenário → ct_id (best-effort, 0076)
        self.live_map = live_map or {}
        self._live_scenario: str | None = None
        self._live_failed = False
        self.status = "queued"  # queued | running | done | failed | timeout | cancelled
        self.log: list[str] = []
        self.subscribers: list[asyncio.Queue] = []
        self.proc: asyncio.subprocess.Process | None = None
        self.queued_at = _now()
        self.started_at: str | None = None
        self.finished_at: str | None = None

    def emit(self, line: str) -> None:
        self.log.append(line)
        for queue in list(self.subscribers):
            queue.put_nowait(line)

    def finish(self, status: str) -> None:
        self.status = status
        self.finished_at = _now()
        for queue in list(self.subscribers):
            queue.put_nowait(None)  # sentinela de fim de stream

    def snapshot(self) -> dict[str, Any]:
        return {
            "exec_id": self.exec_id,
            "target": self.target.get("name"),
            "status": self.status,
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "log_lines": len(self.log),
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunManager:
    def __init__(self, ws: Workspace, conn: sqlite3.Connection):
        self.ws = ws
        self.conn = conn
        self.runs: dict[str, RunInfo] = {}
        self._queues: dict[str, asyncio.Queue] = {}
        self._workers: dict[str, asyncio.Task] = {}

    # -- submissão -------------------------------------------------------

    def submit(
        self,
        target: dict[str, Any],
        testcases: list[dict[str, Any]],
        tags: list[str],
        owner: str = "behave",
        feature: str | None = None,
        features: list[str] | None = None,
        live_map: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Cria a execution (origin local_run) e enfileira o run (FIFO)."""
        execution = exec_ops.create(
            self.ws,
            name=f"Run local {target.get('name')} {_now()[:16]}",
            owner=owner,
            sprint=None,
            environment=target.get("name"),
            testcases=testcases,
            origin="local_run",
        )
        path = exec_ops.save(self.ws, execution)
        reindex_file(self.ws, self.conn, path)

        run = RunInfo(execution["id"], target, tags, feature=feature,
                      features=features, live_map=live_map)
        self.runs[execution["id"]] = run
        name = str(target.get("name"))
        if name not in self._queues:
            self._queues[name] = asyncio.Queue()
            self._workers[name] = asyncio.get_running_loop().create_task(
                self._worker(name)
            )
        self._queues[name].put_nowait(run)
        return execution

    def queue_length(self, target_name: str) -> int:
        queue = self._queues.get(target_name)
        return queue.qsize() if queue else 0

    def cancel(self, exec_id: str) -> RunInfo:
        run = self.runs.get(exec_id)
        if not run:
            raise exec_ops.ExecutionError("not_found", f"run {exec_id} não existe", 404)
        if run.status == "running" and run.proc:
            run.proc.kill()
            run.status = "cancelled"
        elif run.status == "queued":
            run.status = "cancelled"
            run.finish("cancelled")
        return run

    async def shutdown(self) -> None:
        for task in self._workers.values():
            task.cancel()

    # -- execução ---------------------------------------------------------

    async def _worker(self, target_name: str) -> None:
        queue = self._queues[target_name]
        while True:
            run = await queue.get()
            if run.status == "cancelled":
                continue
            try:
                await self._execute(run)
            except Exception as exc:  # nunca derruba o worker do target
                run.emit(f"[arbites] erro interno do runner: {exc}")
                self._mark_pending(run, "blocked", f"runner error: {exc}")
                run.finish("failed")

    async def _execute(self, run: RunInfo) -> None:
        run.status = "running"
        run.started_at = _now()
        target = run.target
        local_path = Path(str(target.get("local_path", "")))
        workdir = Path(tempfile.mkdtemp(prefix=f"arbites-{run.exec_id}-"))
        result_json = workdir / "result.json"
        evidence_dir = workdir / "evidences"
        evidence_dir.mkdir()

        python = str(target.get("python_path") or sys.executable)
        # sem path posicional o behave resolve ./features via cwd=local_path;
        # com run.feature, o arquivo .feature específico entra como posicional
        # (behave <arquivo>.feature --tags=<tag>) — doc de ajustes §1.5.1
        cmd = [
            python, "-m", "behave",
            "-f", "json", "-o", str(result_json),
            "-f", "plain", "--no-capture",
        ]
        if run.tags:
            cmd.append(f"--tags={','.join(run.tags)}")
        cmd.extend(run.features)  # 1..N .feature posicionais (0076)
        run.emit(f"[arbites] $ {' '.join(cmd)}")

        import os

        # 0099: injeta o `.env` do projeto-alvo — sem isto o Behave/WebDriver
        # não vê BASE_URL/LOCAL_BROWSER/credenciais e o browser abre sem destino.
        env = build_run_env(dict(os.environ), local_path, evidence_dir)
        timeout = float(target.get("timeout_minutes") or DEFAULT_TIMEOUT_MINUTES) * 60

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(target.get("working_dir") or local_path),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        run.proc = proc

        async def pump() -> None:
            assert proc.stdout is not None
            while True:
                raw = await proc.stdout.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip()
                run.emit(line)
                self._live_line(run, line)  # progresso ao vivo (best-effort)

        timed_out = False
        try:
            await asyncio.wait_for(pump(), timeout=timeout)
            await proc.wait()
        except asyncio.TimeoutError:
            timed_out = True
            proc.kill()
            await proc.wait()
            run.emit(f"[arbites] timeout após {timeout:.0f}s — processo encerrado")

        cancelled = run.status == "cancelled"
        self._collect(run, result_json, evidence_dir)
        if timed_out:
            self._mark_pending(run, "blocked", "timeout")
            run.finish("timeout")
        elif cancelled:
            self._mark_pending(run, "blocked", "cancelled")
            run.finish("cancelled")
        else:
            run.finish("done")
        shutil.rmtree(workdir, ignore_errors=True)

    def _live_line(self, run: RunInfo, line: str) -> None:
        """Progresso ao vivo por cenário concluído (0076, best-effort).

        Parse do stream plain do behave (EN/PT): ao ver um cenário NOVO,
        conclui o anterior e persiste o resultado parcial na execution —
        o board (refresh) mostra os cards andando. Falha de parse nunca
        derruba o runner; o JSON final SEMPRE reconcilia (_collect)."""
        try:
            m = _LIVE_SCENARIO_RE.match(line)
            if m:
                self._live_conclude(run)
                run._live_scenario = m.group(1)
                run._live_failed = False
                return
            sm = _LIVE_STEP_RE.match(line)
            if sm and sm.group(1) in ("failed", "undefined"):
                run._live_failed = True
        except Exception:
            pass  # live é acessório — nunca crasha o worker

    def _live_conclude(self, run: RunInfo) -> None:
        """Persiste o resultado parcial do cenário corrente (se mapeado)."""
        name = run._live_scenario
        run._live_scenario = None
        if not name:
            return
        ct_id = run.live_map.get(name)
        if not ct_id:
            return
        status = "failed" if run._live_failed else "passed"
        try:
            execution = exec_ops.load(self.ws, run.exec_id)
            exec_ops.set_result_status(execution, ct_id, status, "behave")
            path = exec_ops.save(self.ws, execution)
            reindex_file(self.ws, self.conn, path)
            clear_needs_rerun(self.ws, self.conn, ct_id)  # 0090
            run.emit(f"[arbites] parcial: {ct_id} {status}")
        except Exception:
            pass  # parcial falhou → o JSON final cobre

    def _collect(self, run: RunInfo, result_json: Path, evidence_dir: Path) -> None:
        """Parseia o Cucumber JSON e move evidências dos hooks p/ a execution.

        Fonte OFICIAL do resultado — reconcilia incondicionalmente qualquer
        parcial do progresso ao vivo (skill
        progresso-ao-vivo-fonte-oficial-reconcilia)."""
        self._live_conclude(run)  # fecha o último cenário do live, se houver
        try:
            execution = exec_ops.load(self.ws, run.exec_id)
        except exec_ops.ExecutionError:
            return
        recorded: set[str] = set()  # CTs que receberam resultado neste run (0090)
        if result_json.exists():
            try:
                results = parse_behave_json(
                    result_json.read_bytes(), self.ws.id_prefixes()["testcase"],
                    name_map=run.live_map,
                )
            except BehaveJsonError as exc:
                run.emit(f"[arbites] {exc}")
                results = {}
            for ct_id, scenario in results.items():
                try:
                    result = exec_ops.set_result_status(
                        execution, ct_id, scenario.status, "behave",
                        comment=scenario.scenario_name,
                    )
                except exec_ops.ExecutionError:
                    continue  # cenário de CT que não está nesta execution
                recorded.add(ct_id)
                result["steps"] = scenario.steps
                result["duration_seconds"] = scenario.duration_seconds
                result["error"] = scenario.error
        for ct_dir in sorted(evidence_dir.iterdir()) if evidence_dir.exists() else []:
            if not ct_dir.is_dir():
                continue
            for evidence_file in sorted(ct_dir.rglob("*")):
                if not evidence_file.is_file():
                    continue
                try:
                    exec_ops.add_evidence(
                        self.ws, execution, ct_dir.name,
                        evidence_file.name, evidence_file.read_bytes(),
                        None, "capturada pelo hook do Behave", "behave",
                    )
                except exec_ops.ExecutionError:
                    continue
        path = exec_ops.save(self.ws, execution)
        reindex_file(self.ws, self.conn, path)
        for ct_id in recorded:
            clear_needs_rerun(self.ws, self.conn, ct_id)  # 0090

    def _mark_pending(self, run: RunInfo, status: str, error: str) -> None:
        try:
            execution = exec_ops.load(self.ws, run.exec_id)
        except exec_ops.ExecutionError:
            return
        changed = False
        for result in execution["results"]:
            if result["status"] in ("pending", "in_progress"):
                result["status"] = status
                result["column"] = status
                result["error"] = error
                changed = True
        if changed:
            execution["history"].append(
                {"at": _now(), "who": "arbites", "event": "run_aborted",
                 "reason": error}
            )
            path = exec_ops.save(self.ws, execution)
            reindex_file(self.ws, self.conn, path)
