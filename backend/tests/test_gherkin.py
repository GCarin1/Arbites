"""Critério de aceite pendente da spec indexing (Gherkin pt) + warnings
de integridade do scan (spec local-automation / ADR 0003)."""

import shutil
from pathlib import Path

import pytest
import yaml
from conftest import make_md
from fastapi.testclient import TestClient

from arbites.api import create_app
from arbites.indexer import connect
from arbites.workspace import DEFAULT_CONFIG, Workspace

FIXTURE_REPO = Path(__file__).parent / "fixtures" / "behave_repo"

TC_BODY = "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"


@pytest.fixture()
def auto_ws(tmp_path):
    """Workspace com target apontando para uma cópia do mini-repo Behave."""
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
            "timeout_minutes": 5,
        }
    ]
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    for ct_id, tag in (("CT-9001", "@CT-9001"), ("CT-9002", "@CT-9002")):
        make_md(
            ws.root / "testcases" / f"{ct_id}-auto.md",
            {
                "id": ct_id,
                "title": f"Automatizado {ct_id}",
                "type": "hybrid",
                "status": "ready",
                "automation": {"target": "frontend-web", "scenario_tag": tag},
            },
            TC_BODY,
        )
    # CT automatizado SEM cenário no repo → automação quebrada
    make_md(
        ws.root / "testcases" / "CT-9100-quebrado.md",
        {
            "id": "CT-9100",
            "title": "Sem cenário",
            "type": "automated",
            "status": "ready",
            "automation": {"target": "frontend-web", "scenario_tag": "@CT-9100"},
        },
        "## Objetivo\n\nsteps vivem no .feature\n",
    )
    return ws, repo


@pytest.fixture()
def auto_client(auto_ws):
    ws, repo = auto_ws
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.ws = ws
        client.repo = repo
        yield client


def test_scan_maps_pt_features_by_ct_tag(auto_client):
    ws = auto_client.ws
    conn = connect(ws)
    row = conn.execute(
        "SELECT * FROM scenarios WHERE tag = '@CT-9001'"
    ).fetchone()
    assert row is not None
    assert row["language"] == "pt"
    assert row["scenario_name"] == "Login com credenciais válidas"
    assert row["feature_path"] == "features/login.feature"
    assert row["line"] > 0
    targets = auto_client.get("/api/v1/targets").json()
    assert targets[0]["name"] == "frontend-web"
    assert targets[0]["scenarios"] == 4  # 3 do login.feature + 1 do lento.feature


def test_scan_warnings_orphan_and_broken(auto_client):
    warnings = auto_client.get("/api/v1/warnings").json()
    codes = {(w["code"], w["source_path"]) for w in warnings}
    assert any(c == "orphan_scenario" and "@CT-9099" not in s for c, s in codes) or any(
        w["code"] == "orphan_scenario" and "CT-9099" in w["message"] for w in warnings
    )
    assert any(
        w["code"] == "broken_automation" and "CT-9100" in w["message"] for w in warnings
    )


def test_scan_detects_duplicate_tag(auto_client):
    repo = auto_client.repo
    (repo / "features" / "dup.feature").write_text(
        "# language: pt\nFuncionalidade: Dup\n\n  @CT-9001\n"
        "  Cenário: Duplicado\n    Dado que o usuário está na tela de login\n",
        encoding="utf-8",
    )
    auto_client.post("/api/v1/targets/frontend-web/scan")
    warnings = auto_client.get("/api/v1/warnings").json()
    assert any(w["code"] == "duplicate_scenario_tag" for w in warnings)
