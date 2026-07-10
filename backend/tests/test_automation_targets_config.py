"""CRUD de automation_targets pela UI (sem editar arbites.yaml na mão) e o
scan avulso de .feature usado no form de target ANTES de ele existir.
"""

from pathlib import Path

import yaml

FIXTURE_REPO = Path(__file__).parent / "fixtures" / "behave_repo"


def test_put_targets_persists_to_yaml_and_scans(client):
    resp = client.put(
        "/api/v1/targets",
        json={
            "targets": [
                {
                    "name": "frontend-web",
                    "local_path": str(FIXTURE_REPO),
                    "features_glob": "features/**/*.feature",
                    "timeout_minutes": 15,
                }
            ]
        },
    )
    assert resp.status_code == 200
    out = resp.json()
    assert len(out) == 1
    target = out[0]
    assert target["name"] == "frontend-web"
    assert target["local_path"] == str(FIXTURE_REPO)
    assert target["timeout_minutes"] == 15
    assert target["scenarios"] == 4  # 3 em login.feature + 1 em lento.feature

    # persistiu no arbites.yaml (fonte de verdade — sem precisar editar na mão)
    ws = client.ws
    saved = yaml.safe_load(ws.config_path.read_text(encoding="utf-8"))
    assert saved["automation_targets"][0]["name"] == "frontend-web"

    # GET /targets reflete o mesmo estado
    listed = client.get("/api/v1/targets").json()
    assert listed[0]["scenarios"] == 4


def test_put_targets_replaces_whole_list(client):
    client.put(
        "/api/v1/targets",
        json={"targets": [{"name": "a", "local_path": str(FIXTURE_REPO)}]},
    )
    resp = client.put(
        "/api/v1/targets",
        json={"targets": [{"name": "b", "local_path": str(FIXTURE_REPO)}]},
    )
    names = [t["name"] for t in resp.json()]
    assert names == ["b"]  # "a" não sobrevive — PUT substitui tudo, não faz merge


def test_put_targets_missing_local_path_does_not_crash(client):
    resp = client.put(
        "/api/v1/targets",
        json={"targets": [{"name": "sem-repo", "local_path": "/caminho/que/nao/existe"}]},
    )
    assert resp.status_code == 200
    assert resp.json()[0]["scenarios"] == 0


def test_browse_features_lists_files_with_scenario_counts(client):
    resp = client.get(
        "/api/v1/automation/browse-features",
        params={"local_path": str(FIXTURE_REPO), "features_glob": "features/**/*.feature"},
    )
    assert resp.status_code == 200
    data = resp.json()
    by_path = {f["path"]: f for f in data["features"]}
    assert by_path["features/login.feature"]["scenarios"] == 3
    assert by_path["features/login.feature"]["parseable"] is True
    assert by_path["features/lento.feature"]["scenarios"] == 1


def test_browse_features_default_glob(client):
    resp = client.get(
        "/api/v1/automation/browse-features", params={"local_path": str(FIXTURE_REPO)}
    )
    assert resp.status_code == 200
    paths = [f["path"] for f in resp.json()["features"]]
    assert "features/login.feature" in paths


def test_browse_features_invalid_path_rejected(client):
    resp = client.get(
        "/api/v1/automation/browse-features",
        params={"local_path": "/caminho/que/nao/existe"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_path"


def test_browse_features_narrows_to_single_file(client):
    resp = client.get(
        "/api/v1/automation/browse-features",
        params={"local_path": str(FIXTURE_REPO), "features_glob": "features/login.feature"},
    )
    assert resp.status_code == 200
    paths = [f["path"] for f in resp.json()["features"]]
    assert paths == ["features/login.feature"]
