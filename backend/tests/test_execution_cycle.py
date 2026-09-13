"""Critérios de aceite do ciclo de teste (change 0111, ADR 0013).

A execution é o ciclo: tem período, e cada caso dentro dela tem dono. Não
existe entidade Sprint — `sprint` continua texto livre, agora só como
rótulo de agrupamento. `execution.json` gravado antes destas chaves
continua válido e é lido como ciclo sem período e sem responsável.
"""

import json

from arbites.api import create_app
from arbites.executions import progress
from conftest import ADMIN_EMAIL, login_admin

from fastapi.testclient import TestClient

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir a tela\n2. Agir\n\n"
    "## Resultado esperado\n\nOk.\n"
)


def make_ct(client, title):
    return client.post(
        "/api/v1/testcases", json={"title": title, "body": TC_BODY}
    ).json()


def make_exec(client, ct_ids, **extra):
    return client.post(
        "/api/v1/executions",
        json={"name": "Regressão", "sprint": "Sprint 42",
              "environment": "homolog", "testcase_ids": ct_ids, **extra},
    ).json()


def exec_json_path(client, exec_id="EXEC-0001"):
    return next(client.ws.root.glob(f"executions/*/{exec_id}/execution.json"))


# -- AC1: o ciclo tem período, e um período invertido é recusado -----------


def test_ciclo_nasce_sem_periodo_e_recebe_por_patch(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]])
    assert execution["starts_on"] is None and execution["ends_on"] is None

    patched = client.patch(
        f"/api/v1/executions/{execution['id']}",
        json={"starts_on": "2026-09-01", "ends_on": "2026-09-15"},
    ).json()
    assert patched["starts_on"] == "2026-09-01"
    assert patched["ends_on"] == "2026-09-15"

    # o arquivo é o estado (ADR 0001): o período sobrevive ao processo
    stored = json.loads(exec_json_path(client).read_text(encoding="utf-8"))
    assert stored["starts_on"] == "2026-09-01"


def test_periodo_pode_vir_ja_na_criacao(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]],
                          starts_on="2026-09-01", ends_on="2026-09-15")
    assert (execution["starts_on"], execution["ends_on"]) == ("2026-09-01", "2026-09-15")


def test_ciclo_que_termina_antes_de_comecar_e_recusado(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]])
    resp = client.patch(
        f"/api/v1/executions/{execution['id']}",
        json={"starts_on": "2026-09-15", "ends_on": "2026-09-01"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_period"
    # e nada foi gravado pela metade
    again = client.get(f"/api/v1/executions/{execution['id']}").json()
    assert again["starts_on"] is None and again["ends_on"] is None


def test_data_que_nao_e_data_e_recusada(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]])
    resp = client.patch(
        f"/api/v1/executions/{execution['id']}", json={"starts_on": "15/09/2026"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_date"


def test_uma_ponta_so_do_periodo_e_valida(client):
    """Ciclo com começo e sem fim previsto é normal; não é erro."""
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]])
    patched = client.patch(
        f"/api/v1/executions/{execution['id']}", json={"starts_on": "2026-09-01"},
    ).json()
    assert patched["starts_on"] == "2026-09-01" and patched["ends_on"] is None


# -- AC2: responsável por caso dentro do ciclo -----------------------------


def test_responsavel_por_caso_entra_no_history_e_no_indice(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]])
    exec_id = execution["id"]

    updated = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/assignee",
        json={"assignee": "viewer@arbites.test"},
    ).json()
    assert updated["results"][0]["assignee"] == "viewer@arbites.test"

    evento = [h for h in updated["history"] if h["event"] == "assignee"][-1]
    assert evento["testcase_id"] == ct["id"]
    assert evento["to"] == "viewer@arbites.test"
    # quem atribuiu vem da sessão, não do corpo (capability profile)
    assert evento["who"] == ADMIN_EMAIL

    row = client.app.state.conn.execute(
        "SELECT assignee FROM results WHERE execution_id = ? AND testcase_id = ?",
        (exec_id, ct["id"]),
    ).fetchone()
    assert row["assignee"] == "viewer@arbites.test"


def test_limpar_responsavel_devolve_o_caso_a_ninguem(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]])
    exec_id = execution["id"]
    client.post(f"/api/v1/executions/{exec_id}/results/{ct['id']}/assignee",
                json={"assignee": "viewer@arbites.test"})
    cleared = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/assignee",
        json={"assignee": ""},
    ).json()
    assert cleared["results"][0]["assignee"] is None


def test_dois_casos_do_mesmo_ciclo_em_pessoas_diferentes(client):
    """O ponto do responsável por caso: dividir UMA regressão, não duplicá-la."""
    primeiro, segundo = make_ct(client, "Login"), make_ct(client, "Logout")
    execution = make_exec(client, [primeiro["id"], segundo["id"]])
    exec_id = execution["id"]
    client.post(f"/api/v1/executions/{exec_id}/results/{primeiro['id']}/assignee",
                json={"assignee": "ana@arbites.test"})
    updated = client.post(
        f"/api/v1/executions/{exec_id}/results/{segundo['id']}/assignee",
        json={"assignee": "bruno@arbites.test"},
    ).json()
    donos = {r["testcase_id"]: r["assignee"] for r in updated["results"]}
    assert donos == {primeiro["id"]: "ana@arbites.test",
                     segundo["id"]: "bruno@arbites.test"}


def test_ciclo_fechado_nao_aceita_troca_de_responsavel(client):
    ct = make_ct(client, "Login")
    execution = make_exec(client, [ct["id"]])
    exec_id = execution["id"]
    client.post(f"/api/v1/executions/{exec_id}/results/{ct['id']}/status",
                json={"status": "passed", "who": "carini"})
    client.post(f"/api/v1/executions/{exec_id}/close")
    resp = client.post(f"/api/v1/executions/{exec_id}/results/{ct['id']}/assignee",
                       json={"assignee": "ana@arbites.test"})
    assert resp.status_code == 409


# -- AC3: cabeçalho de progresso e leitura de execution.json antigo --------


def test_contadores_do_cabecalho_fecham_com_o_total(client):
    cts = [make_ct(client, f"CT {i}") for i in range(4)]
    execution = make_exec(client, [c["id"] for c in cts])
    exec_id = execution["id"]
    for ct, status in zip(cts, ["passed", "failed", "blocked"]):
        client.post(f"/api/v1/executions/{exec_id}/results/{ct['id']}/status",
                    json={"status": status, "who": "carini"})

    header = client.get(f"/api/v1/executions/{exec_id}").json()["progress"]
    assert header["total"] == 4
    assert sum(header["counts"].values()) == header["total"]
    assert header["counts"]["passed"] == 1
    assert header["counts"]["pending"] == 1
    # três dos quatro chegaram a um status final
    assert header["done"] == 3 and header["percent"] == 75


def test_ciclo_vazio_de_resultados_nao_divide_por_zero(client):
    """Um ciclo sem casos não é útil, mas também não pode explodir o header."""
    assert progress({"results": []}) == {
        "counts": {"pending": 0, "in_progress": 0, "blocked": 0,
                   "failed": 0, "retest": 0, "passed": 0},
        "total": 0, "done": 0, "percent": 0,
    }


def test_execution_json_antigo_continua_valido(ws):
    """Estrutura aditiva (ADR 0013): o ciclo gravado antes destas chaves é
    lido como ciclo sem período e sem responsável, não como arquivo quebrado."""
    antigo = {
        "schema_version": 1, "id": "EXEC-0001", "name": "Regressão antiga",
        "owner": "carini", "sprint": "Sprint 1", "environment": "homolog",
        "origin": "manual", "created_at": "2026-01-10T12:00:00+00:00",
        "closed_at": None, "status": "in_progress", "ci": None,
        "results": [{"testcase_id": "CT-0001", "status": "passed",
                     "column": "passed", "executed_by": "carini",
                     "executed_at": "2026-01-10T12:30:00+00:00",
                     "duration_seconds": None, "steps": [], "evidences": [],
                     "defects": [], "comment": None, "error": None}],
        "history": [],
    }
    path = ws.root / "executions" / "2026" / "EXEC-0001" / "execution.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(antigo, ensure_ascii=False), encoding="utf-8")

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        login_admin(client)
        lido = client.get("/api/v1/executions/EXEC-0001").json()
        assert lido.get("starts_on") is None
        assert lido["results"][0].get("assignee") is None
        assert lido["progress"] == {
            "counts": {"pending": 0, "in_progress": 0, "blocked": 0,
                       "failed": 0, "retest": 0, "passed": 1},
            "total": 1, "done": 1, "percent": 100,
        }
        # e o ciclo antigo ainda aceita receber o período que faltava
        patched = client.patch("/api/v1/executions/EXEC-0001",
                               json={"starts_on": "2026-01-05"}).json()
        assert patched["starts_on"] == "2026-01-05"
