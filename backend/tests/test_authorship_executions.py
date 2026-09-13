"""Critérios de aceite da autoria em resultado de execução (change 0115).

A capability `profile` já tinha decidido: autoria vem da sessão, nunca do
corpo — "senão a autoria vira um campo que qualquer um preenche com o nome
de qualquer um". As rotas de resultado ficaram de fora e gravavam o `who`
que o cliente mandasse, ou `local` quando ele não mandava nada.
"""

from arbites import auth as auth_ops
from conftest import ADMIN_EMAIL, login_admin

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir\n2. Agir\n\n"
    "## Resultado esperado\n\nOk.\n"
)
OUTRA = {"email": "outra@arbites.test", "password": "senha-de-outra-conta-1"}


def rig(client, quantos=1):
    cts = [
        client.post("/api/v1/testcases",
                    json={"title": f"Caso {i}", "body": TC_BODY}).json()
        for i in range(quantos)
    ]
    execution = client.post(
        "/api/v1/executions",
        json={"name": "Regressão", "testcase_ids": [c["id"] for c in cts]},
    ).json()
    return execution["id"], cts


def eventos(execution, tipo):
    return [h for h in execution["history"] if h["event"] == tipo]


# -- AC1: sem autoria no corpo, a sessão assina ---------------------------


def test_resultado_sem_who_no_corpo_e_assinado_pela_sessao(client):
    """Era este o caso do dia a dia: nenhum cliente do produto mandava `who`,
    e todo resultado manual acabava gravado como `local`."""
    exec_id, (ct,) = rig(client)
    execution = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/status",
        json={"status": "passed", "column": "passed"},
    ).json()

    assert execution["results"][0]["executed_by"] == ADMIN_EMAIL
    assert eventos(execution, "result")[-1]["who"] == ADMIN_EMAIL


def test_passo_evidencia_e_defeito_tambem_sao_assinados_pela_sessao(client):
    exec_id, (ct,) = rig(client)

    passo = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/steps/1",
        json={"status": "passed"},
    ).json()
    assert eventos(passo, "step")[-1]["who"] == ADMIN_EMAIL

    enviado = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/evidences",
        files={"file": ("tela.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert enviado.status_code == 201
    # a autoria da evidência mora no history[] (o registro dela guarda
    # caminho, hash, mime e timestamp — não autor)
    depois = client.get(f"/api/v1/executions/{exec_id}").json()
    assert eventos(depois, "evidence")[-1]["who"] == ADMIN_EMAIL

    defeito = client.post(
        "/api/v1/defects", json={"title": "Bug", "severity": "high"}
    ).json()
    vinculado = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/defects",
        json={"defect_id": defeito["id"]},
    ).json()
    assert eventos(vinculado, "defect")[-1]["who"] == ADMIN_EMAIL


# -- AC2: autoria forjada é recusada, e duas contas não se confundem ------


def test_cliente_que_tenta_forjar_a_autoria_e_recusado(client):
    """Ignorar o campo em silêncio deixaria no contrato uma promessa que o
    servidor não cumpre; 422 diz ao cliente que autoria não se envia."""
    exec_id, (ct,) = rig(client)
    recusado = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/status",
        json={"status": "passed", "column": "passed", "who": "chefe@arbites.test"},
    )
    assert recusado.status_code == 422

    # e nada foi gravado pela metade
    execution = client.get(f"/api/v1/executions/{exec_id}").json()
    assert execution["results"][0]["status"] == "pending"
    assert execution["results"][0]["executed_by"] is None


def test_who_forjado_e_recusado_tambem_no_passo_e_no_defeito(client):
    exec_id, (ct,) = rig(client)
    passo = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/steps/1",
        json={"status": "passed", "who": "chefe@arbites.test"},
    )
    assert passo.status_code == 422

    defeito = client.post(
        "/api/v1/defects", json={"title": "Bug", "severity": "high"}
    ).json()
    vinculo = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/defects",
        json={"defect_id": defeito["id"], "who": "chefe@arbites.test"},
    )
    assert vinculo.status_code == 422


def test_duas_contas_no_mesmo_caso_registram_cada_uma_em_seu_nome(anon_client):
    """O ponto da mudança numa instância de time: a trilha diz quem executou."""
    auth_ops.create_user(
        anon_client.app.state.auth, OUTRA["email"], OUTRA["password"],
        role="editor", status="active",
    )
    login_admin(anon_client)
    exec_id, (ct,) = rig(anon_client)
    anon_client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/status",
        json={"status": "failed", "column": "failed"},
    )
    anon_client.post("/api/v1/auth/logout")

    anon_client.post("/api/v1/auth/login", json={
        "email": OUTRA["email"], "password": OUTRA["password"]})
    execution = anon_client.post(
        f"/api/v1/executions/{exec_id}/results/{ct['id']}/status",
        json={"status": "passed", "column": "passed"},
    ).json()

    assert execution["results"][0]["executed_by"] == OUTRA["email"]
    autores = [e["who"] for e in eventos(execution, "result")]
    assert autores == [ADMIN_EMAIL, OUTRA["email"]]


def test_resultado_de_automacao_continua_assinado_pela_maquina(client):
    """Autor de máquina não é sessão: o que a mudança tira é a autoria vinda
    do CLIENTE, não a distinção entre execução humana e automatizada."""
    from arbites import executions as exec_ops

    exec_id, (ct,) = rig(client)
    execution = exec_ops.load(client.ws, exec_id)
    exec_ops.set_result_status(execution, ct["id"], "passed", "github-actions")
    assert execution["results"][0]["executed_by"] == "github-actions"
