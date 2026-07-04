"""Critérios de aceite da spec executions (SC2)."""

import hashlib
import json

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir a tela\n2. Agir\n3. Conferir\n\n"
    "## Resultado esperado\n\nOk.\n"
)


def make_ct(client, title, **extra):
    return client.post(
        "/api/v1/testcases", json={"title": title, "body": TC_BODY, **extra}
    ).json()


def make_exec(client, name="Regressão", ct_ids=None):
    return client.post(
        "/api/v1/executions",
        json={
            "name": name,
            "sprint": "Sprint 42",
            "environment": "homolog",
            "testcase_ids": ct_ids or [],
            "owner": "carini",
        },
    ).json()


def test_create_snapshots_steps_from_ct(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, ct_ids=[ct["id"]])
    assert execution["id"] == "EXEC-0001"
    assert execution["status"] == "draft"
    result = execution["results"][0]
    assert result["testcase_id"] == ct["id"]
    assert [s["text"] for s in result["steps"]] == [
        "Abrir a tela",
        "Agir",
        "Conferir",
    ]
    # snapshot é imutável: mudar o CT depois não muda o resultado
    client.put(f"/api/v1/testcases/{ct['id']}", json={"body": "## Passos\n\n1. Outro\n"})
    fetched = client.get(f"/api/v1/executions/{execution['id']}").json()
    assert [s["text"] for s in fetched["results"][0]["steps"]][0] == "Abrir a tela"


def test_kanban_move_persists_json_and_history(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, ct_ids=[ct["id"]])
    updated = client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
        json={"status": "passed", "who": "carini"},
    ).json()
    assert updated["status"] == "in_progress"  # draft → in_progress na 1ª atividade
    result = updated["results"][0]
    assert result["status"] == "passed"
    assert result["column"] == "passed"
    events = [e for e in updated["history"] if e["event"] == "result"]
    assert events and events[-1]["to"] == "passed"

    # persistiu no disco (fonte de verdade) e no índice
    ws = client.ws
    files = list((ws.root / "executions").rglob("execution.json"))
    assert len(files) == 1
    on_disk = json.loads(files[0].read_text(encoding="utf-8"))
    assert on_disk["results"][0]["status"] == "passed"
    listed = client.get("/api/v1/executions").json()
    assert listed[0]["result_counts"] == {"passed": 1}


def test_step_marking(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, ct_ids=[ct["id"]])
    updated = client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/steps/2",
        json={"status": "failed", "who": "carini"},
    ).json()
    steps = {s["index"]: s["status"] for s in updated["results"][0]["steps"]}
    assert steps == {1: "pending", 2: "failed", 3: "pending"}


def test_evidence_upload_writes_file_and_sha256(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, ct_ids=[ct["id"]])
    content = b"screenshot-fake-png"
    evidence = client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/evidences",
        files={"file": ("shot.png", content, "image/png")},
        data={"note": "Dashboard após login"},
    ).json()
    assert evidence["sha256"] == hashlib.sha256(content).hexdigest()
    assert evidence["mime"] == "image/png"
    ws = client.ws
    stored = list((ws.root / "executions").rglob("shot.png"))
    assert len(stored) == 1 and stored[0].read_bytes() == content
    assert f"evidences/{ct['id']}/" in evidence["path"]


def test_closed_execution_rejects_changes(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, ct_ids=[ct["id"]])
    closed = client.post(f"/api/v1/executions/{execution['id']}/close").json()
    assert closed["status"] == "closed" and closed["closed_at"]
    resp = client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
        json={"status": "passed"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "execution_closed"


def test_same_ct_different_results_in_two_executions(client):
    ct = make_ct(client, "Login")
    exec_a = make_exec(client, "Sprint A", [ct["id"]])
    exec_b = make_exec(client, "Sprint B", [ct["id"]])
    client.post(
        f"/api/v1/executions/{exec_a['id']}/results/{ct['id']}/status",
        json={"status": "passed"},
    )
    client.post(
        f"/api/v1/executions/{exec_b['id']}/results/{ct['id']}/status",
        json={"status": "failed"},
    )
    a = client.get(f"/api/v1/executions/{exec_a['id']}").json()
    b = client.get(f"/api/v1/executions/{exec_b['id']}").json()
    assert a["results"][0]["status"] == "passed"
    assert b["results"][0]["status"] == "failed"
    # e o documento do CT não mudou (ADR 0005)
    assert client.get(f"/api/v1/testcases/{ct['id']}").json()["status"] == "draft"


def test_execution_survives_index_rebuild(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, ct_ids=[ct["id"]])
    client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
        json={"status": "blocked"},
    )
    client.post("/api/v1/workspace/reindex")
    listed = client.get("/api/v1/executions").json()
    assert listed[0]["id"] == execution["id"]
    assert listed[0]["result_counts"] == {"blocked": 1}
