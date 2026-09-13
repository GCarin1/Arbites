"""GitHub Actions (M4) — dispatch, correlação, polling e coleta por artifact.

Restrição real da API (ADR 0006): logs completos de job só após o término;
ao vivo existe apenas o status de workflow/jobs/steps do workflow. Por
isso a coleta é por artifact (Cucumber JSON), parseado pelo MESMO adapter
do run local (`behave_json`) — executions idênticas nos dois caminhos.

Token: PAT fine-grained via keyring (ADR 0008) — nunca em YAML, nunca no
índice, nunca logado.
"""

from __future__ import annotations

import io
import sqlite3
import time
import zipfile
from datetime import datetime, timezone
from typing import Any, Protocol

from . import executions as exec_ops
from .behave_json import BehaveJsonError, parse_behave_json
from .indexer import clear_needs_rerun, reindex_file
from .workspace import Workspace

KEYRING_SERVICE = "arbites-github"
KEYRING_USER = "pat"
CORRELATION_WINDOW_S = 30
POLL_INTERVAL_S = 10


class CIError(Exception):
    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# ---------------------------------------------------------------------------
# Token (keyring do SO)


class TokenStore:
    def set(self, token: str) -> None:
        import keyring

        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token)

    def get(self) -> str | None:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)

    def status(self) -> dict[str, Any]:
        return {"configured": self.get() is not None}  # nunca o valor


# ---------------------------------------------------------------------------
# Cliente GitHub — interface fina, 1 método ≈ 1 endpoint REST


class GitHubClient(Protocol):
    def dispatch_workflow(self, repo: str, workflow: str, ref: str,
                          inputs: dict[str, str]) -> None: ...
    def list_recent_dispatch_runs(self, repo: str, workflow: str) -> list[dict]: ...
    def get_run(self, repo: str, run_id: int) -> dict: ...
    def get_jobs(self, repo: str, run_id: int) -> list[dict]: ...
    def list_artifacts(self, repo: str, run_id: int) -> list[dict]: ...
    def download_artifact(self, repo: str, artifact_id: int) -> bytes: ...


class HttpxGitHub:
    """Implementação real (httpx) com backoff em rate limit."""

    def __init__(self, tokens: TokenStore):
        self.tokens = tokens

    def _request(self, method: str, path: str, **kwargs) -> Any:
        import httpx

        token = self.tokens.get()
        if not token:
            raise CIError("no_token", "PAT do GitHub não configurado", 409)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        for attempt in range(4):
            resp = httpx.request(
                method, f"https://api.github.com{path}",
                headers=headers, timeout=30, **kwargs,
            )
            if resp.status_code in (403, 429) and attempt < 3:
                time.sleep(2 ** attempt)  # backoff em rate limit (spec)
                continue
            if resp.status_code >= 400:
                raise CIError("github_error",
                              f"GitHub {resp.status_code}: {resp.text[:200]}")
            return resp
        raise CIError("rate_limited", "rate limit persistente na API do GitHub")

    def dispatch_workflow(self, repo, workflow, ref, inputs):
        self._request(
            "POST", f"/repos/{repo}/actions/workflows/{workflow}/dispatches",
            json={"ref": ref, "inputs": inputs},
        )

    def list_recent_dispatch_runs(self, repo, workflow):
        resp = self._request(
            "GET",
            f"/repos/{repo}/actions/workflows/{workflow}/runs"
            "?event=workflow_dispatch&per_page=10",
        )
        return resp.json().get("workflow_runs", [])

    def get_run(self, repo, run_id):
        return self._request("GET", f"/repos/{repo}/actions/runs/{run_id}").json()

    def get_jobs(self, repo, run_id):
        resp = self._request("GET", f"/repos/{repo}/actions/runs/{run_id}/jobs")
        return resp.json().get("jobs", [])

    def list_artifacts(self, repo, run_id):
        resp = self._request("GET", f"/repos/{repo}/actions/runs/{run_id}/artifacts")
        return resp.json().get("artifacts", [])

    def download_artifact(self, repo, artifact_id):
        return self._request(
            "GET", f"/repos/{repo}/actions/artifacts/{artifact_id}/zip",
            follow_redirects=True,
        ).content


# ---------------------------------------------------------------------------
# Orquestração


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CIManager:
    def __init__(self, ws: Workspace, conn: sqlite3.Connection,
                 client: GitHubClient, tokens: TokenStore):
        self.ws = ws
        self.conn = conn
        self.client = client
        self.tokens = tokens

    def _target(self, name: str) -> dict:
        for target in self.ws.config().get("automation_targets") or []:
            if target.get("name") == name:
                github = target.get("github") or {}
                if not github.get("repo") or not github.get("workflow"):
                    raise CIError("no_github",
                                  f"target '{name}' sem bloco github (repo/workflow)",
                                  422)
                return target
        raise CIError("not_found", f"target '{name}' não configurado", 404)

    def dispatch(self, target_name: str, ref: str | None,
                 inputs: dict[str, str], testcases: list[dict]) -> dict:
        """Dispara o workflow e cria a execution github_actions correlacionada."""
        target = self._target(target_name)
        github = target["github"]
        repo, workflow = github["repo"], github["workflow"]
        ref = ref or github.get("ref", "main")

        dispatched_at = datetime.now(timezone.utc)
        self.client.dispatch_workflow(repo, workflow, ref, inputs)

        # a API não retorna o run id do dispatch: correlaciona pelo run mais
        # recente do workflow criado após o dispatch (janela de 30 s)
        run = None
        deadline = time.time() + CORRELATION_WINDOW_S
        while time.time() < deadline:
            for candidate in self.client.list_recent_dispatch_runs(repo, workflow):
                created = candidate.get("created_at", "")
                if created >= dispatched_at.strftime("%Y-%m-%dT%H:%M:%SZ"):
                    run = candidate
                    break
            if run:
                break
            time.sleep(1)
        if not run:
            raise CIError("correlation_failed",
                          "nenhum run do workflow apareceu na janela de 30 s")

        execution = exec_ops.create(
            self.ws,
            name=f"CI {target_name} run {run['id']}",
            owner="github-actions",
            sprint=None,
            environment=target_name,
            testcases=testcases,
            origin="github_actions",
        )
        execution["ci"] = {
            "workflow_run_id": run["id"],
            "run_url": run.get("html_url"),
            "commit_sha": run.get("head_sha"),
            "artifact_id": None,
            "repo": repo,
            "artifact_name": github.get("artifact_name", "cucumber-report"),
        }
        path = exec_ops.save(self.ws, execution)
        reindex_file(self.ws, self.conn, path)
        return execution

    def status(self, exec_id: str) -> dict:
        """Status consolidado: workflow + jobs + steps (do workflow, não Gherkin)."""
        execution = exec_ops.load(self.ws, exec_id)
        ci = execution.get("ci") or {}
        if not ci.get("workflow_run_id"):
            raise CIError("not_ci", f"{exec_id} não é uma execution de CI", 422)
        run = self.client.get_run(ci["repo"], ci["workflow_run_id"])
        jobs = self.client.get_jobs(ci["repo"], ci["workflow_run_id"])
        return {
            "execution_id": exec_id,
            "workflow": {
                "id": run.get("id"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "html_url": run.get("html_url"),
            },
            "jobs": [
                {
                    "name": job.get("name"),
                    "status": job.get("status"),
                    "conclusion": job.get("conclusion"),
                    "steps": [
                        {
                            "name": step.get("name"),
                            "status": step.get("status"),
                            "conclusion": step.get("conclusion"),
                        }
                        for step in job.get("steps", [])
                    ],
                }
                for job in jobs
            ],
            "poll_interval_seconds": POLL_INTERVAL_S,
        }

    def collect(self, exec_id: str) -> dict:
        """Baixa o artifact, parseia o Cucumber JSON e popula a execution."""
        execution = exec_ops.load(self.ws, exec_id)
        ci = execution.get("ci") or {}
        run = self.client.get_run(ci["repo"], ci["workflow_run_id"])
        if run.get("status") != "completed":
            raise CIError("not_completed",
                          f"workflow ainda {run.get('status')}", 409)

        artifacts = self.client.list_artifacts(ci["repo"], ci["workflow_run_id"])
        wanted = ci.get("artifact_name", "cucumber-report")
        artifact = next((a for a in artifacts if a.get("name") == wanted), None)
        if not artifact:
            raise CIError("artifact_missing",
                          f"artifact '{wanted}' não encontrado no run", 404)
        blob = self.client.download_artifact(ci["repo"], artifact["id"])
        execution["ci"]["artifact_id"] = artifact["id"]

        results_found = 0
        recorded: set[str] = set()  # CTs com resultado novo (0090)
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            json_names = [n for n in zf.namelist() if n.endswith(".json")]
            if not json_names:
                raise CIError("artifact_invalid", "artifact sem Cucumber JSON", 422)
            merged: dict = {}
            for name in json_names:
                try:
                    merged.update(
                        parse_behave_json(
                            zf.read(name), self.ws.id_prefixes()["testcase"]
                        )
                    )
                except BehaveJsonError:
                    continue
            if not merged:
                raise CIError("artifact_invalid",
                              "nenhum Cucumber JSON parseável no artifact", 422)
            for ct_id, scenario in merged.items():
                try:
                    result = exec_ops.set_result_status(
                        execution, ct_id, scenario.status, "github-actions",
                        comment=scenario.scenario_name,
                    )
                except exec_ops.ExecutionError:
                    continue
                result["steps"] = scenario.steps
                result["duration_seconds"] = scenario.duration_seconds
                result["error"] = scenario.error
                results_found += 1
                recorded.add(ct_id)
            # screenshots publicados no artifact sob evidences/CT-XXXX/
            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) >= 3 and parts[0] == "evidences" and not name.endswith("/"):
                    ct_id = parts[1]
                    try:
                        exec_ops.add_evidence(
                            self.ws, execution, ct_id, parts[-1], zf.read(name),
                            None, "artifact do GitHub Actions", "github-actions",
                        )
                    except exec_ops.ExecutionError:
                        continue

        path = exec_ops.save(self.ws, execution)
        reindex_file(self.ws, self.conn, path)
        for ct_id in recorded:
            clear_needs_rerun(self.ws, self.conn, ct_id)  # 0090
        return {"execution": execution, "results_collected": results_found}
