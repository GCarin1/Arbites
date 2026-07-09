"""Critérios de aceite da spec ci-automation (SC6) — fake GitHub client.

O cliente real é uma casca fina de 1 método ≈ 1 endpoint REST; o contrato
de orquestração (dispatch → correlação → status → collect) é provado aqui
com um fake em memória e um zip de artifact real.
"""

import io
import json
import time
import zipfile
from datetime import datetime, timezone

import pytest
import yaml
from conftest import make_md
from fastapi.testclient import TestClient

from arbites.api import create_app
from arbites.ci import TokenStore
from arbites.workspace import DEFAULT_CONFIG, Workspace

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def _cucumber_json(ct_id: str, status: str) -> list:
    return [
        {
            "name": "Login",
            "elements": [
                {
                    "type": "scenario",
                    "name": "Login com credenciais válidas",
                    "tags": [ct_id, "smoke"],
                    "status": status,
                    "steps": [
                        {
                            "keyword": "Dado",
                            "name": "que o usuário está na tela de login",
                            "result": {"status": "passed", "duration": 0.5},
                        },
                        {
                            "keyword": "Então",
                            "name": "deve visualizar o dashboard",
                            "result": {
                                "status": status,
                                "duration": 1.0,
                                **(
                                    {"error_message": ["Assertion Failed: erro"]}
                                    if status == "failed"
                                    else {}
                                ),
                            },
                        },
                    ],
                }
            ],
        }
    ]


class FakeGitHub:
    """Simula a API do GitHub Actions: dispatch → run → jobs → artifact."""

    def __init__(self):
        self.runs: dict[int, dict] = {}
        self.artifacts: dict[int, bytes] = {}
        self._next_run = 850
        self.dispatched: list[dict] = []

    def dispatch_workflow(self, repo, workflow, ref, inputs):
        self.dispatched.append(
            {"repo": repo, "workflow": workflow, "ref": ref, "inputs": inputs}
        )
        run_id = self._next_run
        self._next_run += 1
        self.runs[run_id] = {
            "id": run_id,
            "status": "in_progress",
            "conclusion": None,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "head_sha": "abc123",
            "html_url": f"https://github.com/{repo}/actions/runs/{run_id}",
        }

    def list_recent_dispatch_runs(self, repo, workflow):
        return sorted(self.runs.values(), key=lambda r: -r["id"])

    def get_run(self, repo, run_id):
        return self.runs[run_id]

    def get_jobs(self, repo, run_id):
        return [
            {
                "name": "behave",
                "status": self.runs[run_id]["status"],
                "conclusion": self.runs[run_id]["conclusion"],
                "steps": [
                    {"name": "Checkout", "status": "completed", "conclusion": "success"},
                    {"name": "Execute tests",
                     "status": self.runs[run_id]["status"],
                     "conclusion": self.runs[run_id]["conclusion"]},
                ],
            }
        ]

    def list_artifacts(self, repo, run_id):
        return [
            {"id": aid, "name": "cucumber-report"} for aid in self.artifacts
        ]

    def download_artifact(self, repo, artifact_id):
        return self.artifacts[artifact_id]

    # helpers de teste
    def complete_run(self, run_id, ct_id, status="passed", with_screenshot=False):
        self.runs[run_id]["status"] = "completed"
        self.runs[run_id]["conclusion"] = "success" if status == "passed" else "failure"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("result.json", json.dumps(_cucumber_json(ct_id, status)))
            if with_screenshot:
                zf.writestr(f"evidences/{ct_id}/fail-12.png", b"ci-screenshot")
        self.artifacts[991] = buffer.getvalue()


class FakeTokenStore(TokenStore):
    def __init__(self):
        self._token: str | None = None

    def set(self, token: str) -> None:
        self._token = token

    def get(self) -> str | None:
        return self._token


@pytest.fixture()
def ci_client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["automation_targets"] = [
        {
            "name": "frontend-web",
            "kind": "behave",
            "github": {
                "repo": "org/automacao-frontend",
                "workflow": "tests.yml",
                "ref": "main",
                "artifact_name": "cucumber-report",
            },
        }
    ]
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    make_md(
        ws.root / "testcases" / "CT-9001-auto.md",
        {
            "id": "CT-9001",
            "title": "Automatizado",
            "type": "automated",
            "status": "ready",
            "automation": {"target": "frontend-web", "scenario_tag": "@CT-9001"},
        },
        TC_BODY,
    )
    fake = FakeGitHub()
    app = create_app(ws.root, watch=False,
                     github_client=fake, token_store=FakeTokenStore())
    with TestClient(app) as client:
        client.fake = fake
        client.ws = ws
        yield client


def test_dispatch_correlates_run_and_creates_execution(ci_client):
    resp = ci_client.post(
        "/api/v1/runs/ci", json={"target": "frontend-web", "tags": ["@CT-9001"]}
    )
    assert resp.status_code == 201
    execution = resp.json()
    assert execution["origin"] == "github_actions"
    assert execution["ci"]["workflow_run_id"] == 850
    assert execution["ci"]["run_url"].endswith("/runs/850")
    assert execution["ci"]["commit_sha"] == "abc123"
    assert ci_client.fake.dispatched[0]["inputs"] == {"tags": "@CT-9001"}
    assert ci_client.fake.dispatched[0]["ref"] == "main"

    status = ci_client.get(f"/api/v1/runs/ci/{execution['id']}/status").json()
    assert status["workflow"]["status"] == "in_progress"
    assert status["jobs"][0]["steps"][0]["name"] == "Checkout"
    assert status["poll_interval_seconds"] == 10


def test_dispatch_forwards_optional_workflow_inputs(ci_client):
    """Doc §1.5.2: feature/ambiente/navegador/repositório viram inputs."""
    resp = ci_client.post(
        "/api/v1/runs/ci",
        json={
            "target": "frontend-web",
            "tags": ["@CT-9001"],
            "feature": "features/login.feature",
            "environment": "cer",
            "browser": "chrome",
            "source_repo": "org/app-web",
        },
    )
    assert resp.status_code == 201
    inputs = ci_client.fake.dispatched[-1]["inputs"]
    assert inputs["tags"] == "@CT-9001"
    assert inputs["feature"] == "features/login.feature"
    assert inputs["environment"] == "cer"
    assert inputs["browser"] == "chrome"
    assert inputs["source_repo"] == "org/app-web"


def test_collect_produces_execution_identical_to_local_run(ci_client):
    execution = ci_client.post(
        "/api/v1/runs/ci", json={"target": "frontend-web", "tags": ["@CT-9001"]}
    ).json()
    exec_id = execution["id"]

    # coletar antes do fim é rejeitado
    early = ci_client.post(f"/api/v1/runs/ci/{exec_id}/collect")
    assert early.status_code == 409

    ci_client.fake.complete_run(850, "CT-9001", status="failed", with_screenshot=True)
    collected = ci_client.post(f"/api/v1/runs/ci/{exec_id}/collect").json()
    assert collected["results_collected"] == 1

    final = ci_client.get(f"/api/v1/executions/{exec_id}").json()
    result = final["results"][0]
    # mesma estrutura do run local: steps Gherkin, error, evidência hasheada
    assert result["status"] == "failed"
    assert [s["text"] for s in result["steps"]][0].startswith("Dado")
    assert "Assertion Failed" in result["error"]
    assert len(result["evidences"]) == 1
    assert result["evidences"][0]["sha256"]
    assert final["ci"]["artifact_id"] == 991


def test_dispatch_without_github_block_fails_cleanly(ci_client):
    ws = ci_client.ws
    config = yaml.safe_load(ws.config_path.read_text(encoding="utf-8"))
    config["automation_targets"].append({"name": "sem-ci", "kind": "behave"})
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    resp = ci_client.post(
        "/api/v1/runs/ci", json={"target": "sem-ci", "testcase_ids": ["CT-9001"]}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "no_github"
