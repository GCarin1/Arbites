"""Critérios de aceite da spec local-automation (SC5) — behave REAL."""

import shutil
import time
from pathlib import Path

import pytest
import yaml
from conftest import make_md
from fastapi.testclient import TestClient

from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

FIXTURE_REPO = Path(__file__).parent / "fixtures" / "behave_repo"
TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


def _make_ws(tmp_path, timeout_minutes=5.0):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    repo = tmp_path / "auto-repo"
    shutil.copytree(FIXTURE_REPO, repo)
    config = dict(DEFAULT_CONFIG)
    config["automation_targets"] = [
        {
            "name": "frontend-web",
            "kind": "behave",
            "local_path": str(repo),
            "features_glob": "features/**/*.feature",
            "timeout_minutes": timeout_minutes,
        }
    ]
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    for ct_id in ("CT-9001", "CT-9002", "CT-9003"):
        make_md(
            ws.root / "testcases" / f"{ct_id}-auto.md",
            {
                "id": ct_id,
                "title": f"Automatizado {ct_id}",
                "type": "hybrid",
                "status": "ready",
                "automation": {"target": "frontend-web", "scenario_tag": f"@{ct_id}"},
            },
            TC_BODY,
        )
    return ws


def _wait_run(client, exec_id, expect="done", timeout_s=90):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        run = client.get(f"/api/v1/runs/{exec_id}").json()
        if run["status"] in ("done", "failed", "timeout", "cancelled"):
            assert run["status"] == expect, f"run terminou como {run['status']}"
            return run
        time.sleep(0.3)
    raise AssertionError(f"run {exec_id} não terminou em {timeout_s}s")


@pytest.fixture()
def auto_client(tmp_path):
    ws = _make_ws(tmp_path)
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.ws = ws
        yield client


def test_local_run_populates_execution_with_gherkin_steps_and_evidence(auto_client):
    resp = auto_client.post(
        "/api/v1/runs/local",
        json={"target": "frontend-web", "testcase_ids": ["CT-9001", "CT-9002"]},
    )
    assert resp.status_code == 201
    exec_id = resp.json()["execution"]["id"]
    assert resp.json()["execution"]["origin"] == "local_run"

    _wait_run(auto_client, exec_id)

    execution = auto_client.get(f"/api/v1/executions/{exec_id}").json()
    by_ct = {r["testcase_id"]: r for r in execution["results"]}
    passed = by_ct["CT-9001"]
    assert passed["status"] == "passed"
    # steps são os steps GHERKIN do cenário, não os do .md
    texts = [s["text"] for s in passed["steps"]]
    assert len(texts) == 3
    assert texts[0].startswith(("Dado", "Given"))
    assert all(s["status"] == "passed" for s in passed["steps"])

    failed = by_ct["CT-9002"]
    assert failed["status"] == "failed"
    assert failed["error"] and "falha esperada" in failed["error"]
    # evidência capturada pelo hook (contrato ARBITES_EVIDENCE_DIR), hasheada
    assert len(failed["evidences"]) == 1
    evidence = failed["evidences"][0]
    assert evidence["sha256"] and evidence["path"].startswith("evidences/CT-9002/")
    ws = auto_client.ws
    stored = list((ws.root / "executions").rglob("fail-*.png"))
    assert len(stored) == 1

    # log ao vivo: o stream (após o fim) devolve o buffer e fecha
    stream = auto_client.get(f"/api/v1/runs/{exec_id}/stream")
    assert stream.status_code == 200
    assert "event: done" in stream.text
    assert "behave" in stream.text or "Cen" in stream.text or "Feature" in stream.text


def test_two_runs_same_target_are_fifo(auto_client):
    first = auto_client.post(
        "/api/v1/runs/local",
        json={"target": "frontend-web", "testcase_ids": ["CT-9001"]},
    ).json()
    second = auto_client.post(
        "/api/v1/runs/local",
        json={"target": "frontend-web", "testcase_ids": ["CT-9002"]},
    ).json()
    run1 = _wait_run(auto_client, first["execution"]["id"])
    run2 = _wait_run(auto_client, second["execution"]["id"])
    # exclusão mútua + ordem: o segundo só começa depois do primeiro acabar
    assert run2["started_at"] >= run1["finished_at"]


def test_timeout_marks_pending_as_blocked(tmp_path):
    ws = _make_ws(tmp_path, timeout_minutes=0.05)  # 3 s
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.ws = ws
        resp = client.post(
            "/api/v1/runs/local",
            json={"target": "frontend-web", "testcase_ids": ["CT-9003"]},
        )
        exec_id = resp.json()["execution"]["id"]
        _wait_run(client, exec_id, expect="timeout", timeout_s=60)
        execution = client.get(f"/api/v1/executions/{exec_id}").json()
        result = execution["results"][0]
        assert result["status"] == "blocked"
        assert result["error"] == "timeout"


def test_selection_by_tags_resolves_cts(auto_client):
    resp = auto_client.post(
        "/api/v1/runs/local",
        json={"target": "frontend-web", "tags": ["@CT-9001"]},
    )
    assert resp.status_code == 201
    execution = resp.json()["execution"]
    assert [r["testcase_id"] for r in execution["results"]] == ["CT-9001"]
    _wait_run(auto_client, execution["id"])


def test_run_whole_feature_without_any_ct_tag_does_not_422(tmp_path):
    """Bug real (mudança 0067): repositório sem nenhuma tag @CT- (comum no
    primeiro uso, antes do time adotar a convenção) fazia o dropdown de
    features ficar vazio e o run devolver 422 empty_selection mesmo com um
    .feature válido selecionado. Rodar o arquivo inteiro deve funcionar
    mesmo sem nenhum cenário mapeado a um CT — o vínculo por tag é o
    caminho para rastreabilidade, não um pré-requisito para executar."""
    ws = _make_ws(tmp_path)
    repo = Path(ws.config()["automation_targets"][0]["local_path"])
    (repo / "features" / "sem_tag.feature").write_text(
        "# language: pt\nFuncionalidade: Sem tag\n\n"
        "  Cenário: sem vínculo a CT\n    Dado que o usuário está na tela de login\n",
        encoding="utf-8",
    )
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.ws = ws
        resp = client.post(
            "/api/v1/runs/local",
            json={"target": "frontend-web", "feature": "features/sem_tag.feature"},
        )
        assert resp.status_code == 201  # não 422 empty_selection
        execution = resp.json()["execution"]
        assert execution["results"] == []  # nenhum CT vinculado, e tudo bem

        _wait_run(client, execution["id"])
        stream = client.get(f"/api/v1/runs/{execution['id']}/stream")
        assert "sem_tag.feature" in stream.text  # o behave rodou o arquivo
