"""Automação reformulada (doc §1.5): features/tags, artefatos, .env, CI params."""

import pytest


@pytest.fixture()
def target(client, tmp_path):
    """Target apontando para um repo fake com features/artefatos/.env."""
    repo = tmp_path / "auto-repo"
    (repo / "features").mkdir(parents=True)
    (repo / "features" / "login.feature").write_text(
        "Feature: Login\n\n  @CT-0001\n  Scenario: ok\n    Given x\n", encoding="utf-8"
    )
    (repo / "logs").mkdir()
    (repo / "logs" / "run.log").write_text("linha de log", encoding="utf-8")
    (repo / "screenshots").mkdir()
    (repo / "analise").mkdir()
    (repo / ".env").write_text(
        "# comentário preservado\nBASE_URL=http://old\nHEADLESS=false\n", encoding="utf-8"
    )
    import yaml
    cfg = client.ws.config()
    cfg["automation_targets"] = [{"name": "web", "kind": "behave",
                                  "local_path": str(repo), "features_glob": "features/**/*.feature"}]
    client.ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    client.post("/api/v1/targets/web/scan")
    return repo


def test_target_features_and_tags(client, target):
    data = client.get("/api/v1/targets/web/features").json()
    assert data["features"] and data["features"][0]["path"].endswith("login.feature")
    assert "@CT-0001" in data["tags"]


def test_artifacts_listing_and_download(client, target):
    arts = client.get("/api/v1/targets/web/artifacts").json()
    assert [f["path"] for f in arts["logs"]] == ["run.log"]
    assert arts["screenshots"] == [] and arts["analise"] == []
    resp = client.get(
        "/api/v1/targets/web/artifacts/file",
        params={"kind": "logs", "path": "run.log"},
    )
    assert resp.status_code == 200 and "linha de log" in resp.text
    # traversal bloqueado
    assert client.get(
        "/api/v1/targets/web/artifacts/file",
        params={"kind": "logs", "path": "../.env"},
    ).status_code == 404


def test_env_editor_preserves_comments_and_unknown_lines(client, target):
    # 0099: o catálogo deriva do .env/.env.example do próprio target
    catalog = client.get("/api/v1/env/catalog", params={"target": "web"}).json()["catalog"]
    assert any(v["key"] == "BASE_URL" for v in catalog)
    assert any(v["key"] == "HEADLESS" for v in catalog)
    env = client.get("/api/v1/targets/web/env").json()
    assert env["values"]["BASE_URL"] == "http://old"

    client.put(
        "/api/v1/targets/web/env",
        json={"values": {"BASE_URL": "http://new", "TEST_DOCUMENTO": "123"}},
    )
    text = (target / ".env").read_text(encoding="utf-8")
    assert "# comentário preservado" in text  # comentário intacto
    assert "BASE_URL=http://new" in text
    assert "HEADLESS=false" in text  # linha não tocada permanece
    assert "TEST_DOCUMENTO=123" in text  # chave nova ao final
