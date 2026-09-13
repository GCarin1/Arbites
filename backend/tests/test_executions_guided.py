"""Critérios de aceite do modo guiado (change 0113).

O modo guiado não tem endpoint próprio: ele é outra leitura da mesma
execution que o Kanban lê e escreve. O que estes testes provam é a
SEQUÊNCIA que a tela executa — percorrer a fila, dar resultado, avançar,
parar no último — contra a API real, para que a regra de avanço não viva
apenas no componente.
"""

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir a tela\n2. Agir\n\n"
    "## Resultado esperado\n\nOk.\n"
)

PENDING = {"pending", "in_progress"}


def make_ct(client, title):
    return client.post(
        "/api/v1/testcases", json={"title": title, "body": TC_BODY}
    ).json()


def make_cycle(client, quantos=3):
    cts = [make_ct(client, f"Caso {i}") for i in range(quantos)]
    execution = client.post(
        "/api/v1/executions",
        json={"name": "Regressão guiada", "sprint": "Sprint 42",
              "environment": "homolog",
              "testcase_ids": [c["id"] for c in cts]},
    ).json()
    return execution, cts


def fila(execution):
    """A fila que o modo guiado percorre: casos sem resultado final."""
    return [r["testcase_id"] for r in execution["results"]
            if (r["column"] or r["status"]) in PENDING]


def proximo_pendente(execution, atual):
    """A regra de avanço da tela: o próximo pendente DEPOIS do atual."""
    ids = [r["testcase_id"] for r in execution["results"]]
    adiante = ids[ids.index(atual) + 1:]
    pendentes = set(fila(execution))
    return next((ct for ct in adiante if ct in pendentes), None)


def resolver(client, exec_id, ct_id, status="passed"):
    return client.post(
        f"/api/v1/executions/{exec_id}/results/{ct_id}/status",
        json={"status": status, "column": status, "who": "carini"},
    )


# -- AC1: percorre na ordem, grava na mesma execution ---------------------


def test_percorre_o_ciclo_na_ordem_dando_resultado_e_avancando(client):
    execution, cts = make_cycle(client, 3)
    exec_id = execution["id"]
    atual = fila(execution)[0]
    assert atual == cts[0]["id"]

    visitados = [atual]
    while atual:
        execution = resolver(client, exec_id, atual).json()
        atual = proximo_pendente(execution, atual)
        if atual:
            visitados.append(atual)

    assert visitados == [c["id"] for c in cts]
    assert fila(execution) == []


def test_o_que_o_modo_guiado_grava_e_a_mesma_execution_que_o_kanban_le(client):
    """Sem endpoint novo: o Kanban relê o mesmo `execution.json`."""
    execution, cts = make_cycle(client, 2)
    exec_id = execution["id"]
    resolver(client, exec_id, cts[0]["id"], "failed")

    do_kanban = client.get(f"/api/v1/executions/{exec_id}").json()
    resultado = next(r for r in do_kanban["results"]
                     if r["testcase_id"] == cts[0]["id"])
    assert resultado["status"] == "failed" and resultado["column"] == "failed"
    # e o cabeçalho do ciclo (change 0111) enxerga o mesmo avanço
    assert do_kanban["progress"]["done"] == 1
    assert do_kanban["progress"]["total"] == 2


def test_evidencia_e_comentario_do_caso_ativo_gravam_sem_modal(client):
    """O painel do caso ativo é o MESMO do Kanban, sem o modal em volta: o
    que ele grava tem de aparecer no resultado do jeito de sempre."""
    execution, cts = make_cycle(client, 1)
    exec_id, ct_id = execution["id"], cts[0]["id"]

    client.post(f"/api/v1/executions/{exec_id}/results/{ct_id}/steps/1",
                json={"status": "passed", "who": "carini"})
    enviado = client.post(
        f"/api/v1/executions/{exec_id}/results/{ct_id}/evidences",
        files={"file": ("tela.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        data={"who": "carini"},
    )
    assert enviado.status_code == 201

    depois = resolver(client, exec_id, ct_id).json()
    resultado = depois["results"][0]
    assert resultado["steps"][0]["status"] == "passed"
    assert len(resultado["evidences"]) == 1
    assert resultado["status"] == "passed"


def test_caso_ja_resolvido_sai_da_fila_mas_continua_visitavel(client):
    """A fila some, a lista não: o QA ainda precisa poder voltar e olhar."""
    execution, cts = make_cycle(client, 3)
    exec_id = execution["id"]
    execution = resolver(client, exec_id, cts[1]["id"], "blocked").json()

    assert cts[1]["id"] not in fila(execution)
    assert len(execution["results"]) == 3
    assert proximo_pendente(execution, cts[0]["id"]) == cts[2]["id"]


# -- AC2: fim da fila e ciclo fechado -------------------------------------


def test_resultado_no_ultimo_pendente_encerra_a_fila(client):
    """Parar é o certo: dar a volta faria o QA revisitar o que acabou de
    fechar sem perceber."""
    execution, cts = make_cycle(client, 2)
    exec_id = execution["id"]
    resolver(client, exec_id, cts[0]["id"])
    execution = resolver(client, exec_id, cts[1]["id"]).json()

    assert proximo_pendente(execution, cts[1]["id"]) is None
    assert fila(execution) == []


def test_ciclo_fechado_e_percorrivel_mas_nao_gravavel(client):
    execution, cts = make_cycle(client, 2)
    exec_id = execution["id"]
    for ct in cts:
        resolver(client, exec_id, ct["id"])
    client.post(f"/api/v1/executions/{exec_id}/close")

    lido = client.get(f"/api/v1/executions/{exec_id}").json()
    assert lido["status"] == "closed"
    assert len(lido["results"]) == 2  # percorrível

    recusado = resolver(client, exec_id, cts[0]["id"], "failed")
    assert recusado.status_code == 409  # não gravável


def test_ciclo_sem_casos_nao_tem_fila_para_percorrer(client):
    """A tela cai no estado vazio em vez de tentar abrir um caso ativo."""
    vazio = client.post(
        "/api/v1/executions",
        json={"name": "Sem casos", "testcase_ids": []},
    )
    assert vazio.status_code == 422
    assert vazio.json()["error"]["code"] == "empty_execution"
