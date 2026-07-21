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


def test_multi_feature_run_creates_one_execution_with_all_cts(auto_client):
    """0076: 1..N .feature de features diferentes numa execution só."""
    repo = Path(auto_client.ws.config()["automation_targets"][0]["local_path"])
    resp = auto_client.post(
        "/api/v1/runs/local",
        json={
            "target": "frontend-web",
            "features": ["features/login.feature", "features/lento.feature"],
        },
    )
    assert resp.status_code == 201
    execution = resp.json()["execution"]
    ids = {r["testcase_id"] for r in execution["results"]}
    # login tem CT-9001/9002 (+ órfão 9099 sem CT espelho); lento tem CT-9003
    assert {"CT-9001", "CT-9002", "CT-9003"} <= ids
    assert repo.exists()
    _wait_run(auto_client, execution["id"], expect="done", timeout_s=90)


def test_runs_active_reflects_running_then_empties(auto_client):
    """0076: /runs/active mostra o run em andamento e esvazia ao terminar."""
    resp = auto_client.post(
        "/api/v1/runs/local",
        json={"target": "frontend-web", "testcase_ids": ["CT-9001"]},
    )
    exec_id = resp.json()["execution"]["id"]
    active = auto_client.get("/api/v1/runs/active").json()
    assert active["count"] >= 1
    assert any(r["exec_id"] == exec_id for r in active["runs"])

    _wait_run(auto_client, exec_id)
    active = auto_client.get("/api/v1/runs/active").json()
    assert all(r["exec_id"] != exec_id for r in active["runs"])


def test_live_progress_reconciled_by_final_json(auto_client):
    """0076: o progresso ao vivo é best-effort e o JSON final SEMPRE
    reconcilia — no fim, os resultados batem com o comportamento real
    (CT-9001 passed, CT-9002 failed), independentemente do parcial."""
    resp = auto_client.post(
        "/api/v1/runs/local",
        json={"target": "frontend-web", "testcase_ids": ["CT-9001", "CT-9002"]},
    )
    exec_id = resp.json()["execution"]["id"]
    _wait_run(auto_client, exec_id)
    execution = auto_client.get(f"/api/v1/executions/{exec_id}").json()
    by_ct = {r["testcase_id"]: r["status"] for r in execution["results"]}
    assert by_ct == {"CT-9001": "passed", "CT-9002": "failed"}
    # o stream registrou parciais ao vivo (best-effort) antes do fim
    stream = auto_client.get(f"/api/v1/runs/{exec_id}/stream")
    assert "[arbites] parcial:" in stream.text


# -- 0099: injeção do .env do projeto no ambiente do run ----------------------

from arbites.runner import build_run_env, load_env_file  # noqa: E402


def test_load_env_file_parses_and_ignores_noise(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "# comentário de topo\n"
        'BASE_URL="https://app.test"\n'
        "export LOCAL_BROWSER=chrome\n"
        "VAZIO=\n"
        "\n"
        "linha inválida sem igual\n"
        "HEADLESS='false'\n",
        encoding="utf-8",
    )
    vals = load_env_file(p)
    assert vals["BASE_URL"] == "https://app.test"
    assert vals["LOCAL_BROWSER"] == "chrome"  # prefixo export removido
    assert vals["VAZIO"] == ""
    assert vals["HEADLESS"] == "false"
    assert "linha inválida sem igual" not in vals


def test_load_env_file_missing_is_empty(tmp_path):
    assert load_env_file(tmp_path / "nao-existe.env") == {}


def test_build_run_env_injects_project_env_but_arbites_keys_win(tmp_path):
    (tmp_path / ".env").write_text(
        "BASE_URL=https://app.test\n"
        "ARBITES_EVIDENCE_DIR=/tentativa/de/sobrescrever\n"
        "PYTHONIOENCODING=latin-1\n",
        encoding="utf-8",
    )
    evidence = tmp_path / "ev"
    env = build_run_env({"PATH": "/bin"}, tmp_path, evidence)
    assert env["BASE_URL"] == "https://app.test"  # projeto injetado no subprocess
    assert env["PATH"] == "/bin"  # base preservada
    # o .env do projeto NUNCA sobrescreve as chaves de controle do Arbites
    assert env["ARBITES_EVIDENCE_DIR"] == str(evidence)
    assert env["PYTHONIOENCODING"] == "utf-8"
