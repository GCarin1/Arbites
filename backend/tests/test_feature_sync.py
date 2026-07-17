"""Sync .feature ↔ CT por NOME de cenário (mudança 0075).

Repo de automação read-only (ADR 0003): o vínculo alternativo à tag é
automation.feature_path + scenario_name. A sync classifica cada cenário
(linked_tag/linked/modified/new + broken) e o apply cria/atualiza/re-vincula
apenas o que o usuário selecionou."""

import yaml


def _repo(tmp_path, login_extra=""):
    repo = tmp_path / "sync-repo"
    (repo / "features").mkdir(parents=True, exist_ok=True)
    (repo / "features" / "login.feature").write_text(
        "Feature: Login\n\n"
        "  @CT-9001\n"
        "  Scenario: com tag\n    Given x\n\n"
        "  Scenario: sem tag ainda\n    Given passo um\n    When passo dois\n"
        + login_extra,
        encoding="utf-8",
    )
    return repo


def _configure(client, repo):
    cfg = client.ws.config()
    cfg["automation_targets"] = [{
        "name": "web", "kind": "behave", "local_path": str(repo),
        "features_glob": "features/**/*.feature",
    }]
    client.ws.config_path.write_text(
        yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8"
    )
    client.post("/api/v1/targets/web/scan")


def test_sync_status_classifies_new_and_linked_tag(client, tmp_path):
    _configure(client, _repo(tmp_path))
    data = client.get(
        "/api/v1/automation/features-sync", params={"target": "web"}
    ).json()
    sc = {s["name"]: s for s in data["features"][0]["scenarios"]}
    assert sc["com tag"]["status"] == "linked_tag"
    assert sc["sem tag ainda"]["status"] == "new"
    assert data["broken"] == []


def test_apply_create_links_by_name_and_next_sync_is_linked(client, tmp_path):
    repo = _repo(tmp_path)
    _configure(client, repo)
    resp = client.post(
        "/api/v1/automation/features-sync/apply",
        json={"target": "web", "create": [
            {"feature_path": "features/login.feature", "scenario_name": "sem tag ainda"}
        ]},
    )
    assert resp.status_code == 200
    created = resp.json()["created"]
    assert len(created) == 1
    ct = client.get(f"/api/v1/testcases/{created[0]}").json()
    assert ct["title"] == "sem tag ainda"
    assert ct["type"] == "automated"
    assert "Given passo um" in ct["body"]  # steps verbatim

    # o .feature segue INTOCADO (repo read-only, ADR 0003)
    text = (repo / "features" / "login.feature").read_text(encoding="utf-8")
    assert created[0] not in text

    data = client.get(
        "/api/v1/automation/features-sync", params={"target": "web"}
    ).json()
    sc = {s["name"]: s for s in data["features"][0]["scenarios"]}
    assert sc["sem tag ainda"]["status"] == "linked"
    assert sc["sem tag ainda"]["ct_id"] == created[0]


def test_sync_detects_modified_steps_and_update_rebases(client, tmp_path):
    repo = _repo(tmp_path)
    _configure(client, repo)
    created = client.post(
        "/api/v1/automation/features-sync/apply",
        json={"target": "web", "create": [
            {"feature_path": "features/login.feature", "scenario_name": "sem tag ainda"}
        ]},
    ).json()["created"]

    # edita os steps do cenário no .feature
    f = repo / "features" / "login.feature"
    f.write_text(
        f.read_text(encoding="utf-8").replace("When passo dois", "When passo MUDOU"),
        encoding="utf-8",
    )

    data = client.get(
        "/api/v1/automation/features-sync", params={"target": "web"}
    ).json()
    sc = {s["name"]: s for s in data["features"][0]["scenarios"]}
    assert sc["sem tag ainda"]["status"] == "modified"

    client.post(
        "/api/v1/automation/features-sync/apply",
        json={"target": "web", "update": created},
    )
    ct = client.get(f"/api/v1/testcases/{created[0]}").json()
    assert "passo MUDOU" in ct["body"]
    data = client.get(
        "/api/v1/automation/features-sync", params={"target": "web"}
    ).json()
    sc = {s["name"]: s for s in data["features"][0]["scenarios"]}
    assert sc["sem tag ainda"]["status"] == "linked"


def test_sync_detects_broken_on_rename_and_relink_fixes(client, tmp_path):
    repo = _repo(tmp_path)
    _configure(client, repo)
    created = client.post(
        "/api/v1/automation/features-sync/apply",
        json={"target": "web", "create": [
            {"feature_path": "features/login.feature", "scenario_name": "sem tag ainda"}
        ]},
    ).json()["created"]

    # renomeia o cenário → vínculo por nome quebra
    f = repo / "features" / "login.feature"
    f.write_text(
        f.read_text(encoding="utf-8").replace(
            "Scenario: sem tag ainda", "Scenario: renomeado"
        ),
        encoding="utf-8",
    )

    data = client.get(
        "/api/v1/automation/features-sync", params={"target": "web"}
    ).json()
    assert data["broken"] == [{
        "ct_id": created[0], "feature_path": "features/login.feature",
        "scenario_name": "sem tag ainda",
    }]
    sc = {s["name"]: s for s in data["features"][0]["scenarios"]}
    assert sc["renomeado"]["status"] == "new"

    client.post(
        "/api/v1/automation/features-sync/apply",
        json={"target": "web", "relink": [{
            "ct_id": created[0], "feature_path": "features/login.feature",
            "scenario_name": "renomeado",
        }]},
    )
    data = client.get(
        "/api/v1/automation/features-sync", params={"target": "web"}
    ).json()
    assert data["broken"] == []
    sc = {s["name"]: s for s in data["features"][0]["scenarios"]}
    assert sc["renomeado"]["status"] == "linked"
    assert sc["renomeado"]["ct_id"] == created[0]


def test_name_linked_ct_resolves_in_feature_run_selection(client, tmp_path):
    """CT vinculado por nome entra na execution ao rodar o .feature inteiro
    (resolução via ct_id na tabela scenarios)."""
    _configure(client, _repo(tmp_path))
    created = client.post(
        "/api/v1/automation/features-sync/apply",
        json={"target": "web", "create": [
            {"feature_path": "features/login.feature", "scenario_name": "sem tag ainda"}
        ]},
    ).json()["created"]

    resp = client.post(
        "/api/v1/runs/local",
        json={"target": "web", "feature": "features/login.feature"},
    )
    assert resp.status_code == 201
    ids = [r["testcase_id"] for r in resp.json()["execution"]["results"]]
    assert created[0] in ids  # o name-linked entrou na execution
