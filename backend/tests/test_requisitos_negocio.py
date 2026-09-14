"""Requisito é insumo do time de NEGÓCIO (change 0158).

Três perguntas que a tela passa a responder, e que a anterior não respondia:
"este critério foi verificado?" (não: "quantos casos a story tem?"), "de quem
é este requisito?" e "posso editar isto aqui sem criar divergência?".
"""

import pytest
from conftest import login_admin

CORPO_STORY = """## Critérios de aceite

- [EARS-1] The system shall exibir o saldo na abertura da tela.
- [EARS-2] When o saldo for negativo, the system shall destacá-lo em vermelho.
- [EARS-3] The system shall permitir exportar o extrato em CSV.
"""

CORPO_CT = "## Passos\n\n1. abrir\n\n## Resultado esperado\n\nabre\n"


def _story(client) -> str:
    return client.post("/api/v1/requirements", json={
        "kind": "story", "title": "Extrato da conta", "body": CORPO_STORY,
    }).json()["id"]


def _caso(client, story: str, criterios: list[str], titulo="Caso") -> str:
    return client.post("/api/v1/testcases", json={
        "title": titulo, "body": CORPO_CT, "story": story, "criteria": criterios,
    }).json()["id"]


# -- cobertura POR CRITÉRIO --------------------------------------------------


def test_criterio_sem_caso_aparece_descoberto(client):
    """"A story tem 4 CTs" não responde a pergunta do negócio: quatro casos
    podem cobrir o mesmo critério e deixar três descobertos."""
    story = _story(client)
    _caso(client, story, ["EARS-1"], "Só o primeiro")

    criterios = client.get(f"/api/v1/requirements/{story}/criteria").json()
    por_id = {c["ears_id"]: c for c in criterios}

    assert por_id["EARS-1"]["coverage"] == "untested"
    assert [c["id"] for c in por_id["EARS-1"]["covered_by"]]
    assert por_id["EARS-2"]["coverage"] == "uncovered"
    assert por_id["EARS-2"]["covered_by"] == []
    assert por_id["EARS-3"]["coverage"] == "uncovered"


def test_cobertura_do_criterio_segue_o_ultimo_resultado(client):
    story = _story(client)
    ct = _caso(client, story, ["EARS-1"])
    execucao = client.post("/api/v1/executions", json={
        "name": "Ciclo", "owner": "qa", "testcase_ids": [ct]}).json()["id"]

    client.post(f"/api/v1/executions/{execucao}/results/{ct}/status",
                json={"status": "passed"})
    criterios = {c["ears_id"]: c for c in
                 client.get(f"/api/v1/requirements/{story}/criteria").json()}
    assert criterios["EARS-1"]["coverage"] == "passing"

    client.post(f"/api/v1/executions/{execucao}/results/{ct}/status",
                json={"status": "failed"})
    criterios = {c["ears_id"]: c for c in
                 client.get(f"/api/v1/requirements/{story}/criteria").json()}
    assert criterios["EARS-1"]["coverage"] == "failing"


def test_um_caso_falhando_basta_para_o_criterio_nao_estar_verificado(client):
    """Dois casos cobrem o critério; um passa e o outro falha. Chamar isso de
    "verificado" seria a média escondendo o defeito."""
    story = _story(client)
    bom = _caso(client, story, ["EARS-1"], "Passa")
    ruim = _caso(client, story, ["EARS-1"], "Falha")
    execucao = client.post("/api/v1/executions", json={
        "name": "Ciclo", "owner": "qa", "testcase_ids": [bom, ruim]}).json()["id"]
    client.post(f"/api/v1/executions/{execucao}/results/{bom}/status",
                json={"status": "passed"})
    client.post(f"/api/v1/executions/{execucao}/results/{ruim}/status",
                json={"status": "failed"})

    criterios = {c["ears_id"]: c for c in
                 client.get(f"/api/v1/requirements/{story}/criteria").json()}
    assert criterios["EARS-1"]["coverage"] == "failing"
    assert len(criterios["EARS-1"]["covered_by"]) == 2


# -- de quem é o requisito ---------------------------------------------------


def test_requisito_escrito_aqui_se_declara_local(client):
    story = _story(client)
    req = client.get(f"/api/v1/requirements/{story}").json()
    assert req["owned_elsewhere"] is False
    assert req["external"] == []


def test_requisito_vinculado_se_declara_externo(client):
    story = _story(client)
    client.put(f"/api/v1/integrations/links/requirement/{story}",
               json={"system": "businessmap", "id": "CARD-77"})

    req = client.get(f"/api/v1/requirements/{story}").json()
    assert req["owned_elsewhere"] is True
    assert req["external"][0]["system"] == "businessmap"


# -- edição recusada quando ele vive lá --------------------------------------


def test_editar_requisito_que_vive_no_sistema_oficial_e_recusado(client):
    """Editar a cópia produz divergência SILENCIOSA: os dois lados passam a
    discordar e ninguém é avisado, porque nada falha."""
    story = _story(client)
    client.put(f"/api/v1/integrations/links/requirement/{story}",
               json={"system": "businessmap", "id": "CARD-77"})

    r = client.put(f"/api/v1/requirements/{story}",
                   json={"title": "Título mudado por aqui"})
    assert r.status_code == 409
    erro = r.json()["error"]
    assert erro["code"] == "owned_elsewhere"
    assert "businessmap" in erro["message"]
    # e a recusa ENSINA a saída, em vez de só barrar
    assert "remova o vínculo" in erro["message"]

    # nada foi gravado
    assert client.get(f"/api/v1/requirements/{story}").json()["title"] == (
        "Extrato da conta")


def test_remover_o_vinculo_devolve_a_edicao(client):
    """A saída existe e é explícita: assumir o requisito aqui é uma decisão
    registrada, não um contorno."""
    story = _story(client)
    client.put(f"/api/v1/integrations/links/requirement/{story}",
               json={"system": "businessmap", "id": "CARD-77"})
    assert client.put(f"/api/v1/requirements/{story}",
                      json={"title": "x"}).status_code == 409

    client.delete(f"/api/v1/integrations/links/requirement/{story}/businessmap")

    ok = client.put(f"/api/v1/requirements/{story}", json={"title": "Agora sim"})
    assert ok.status_code == 200
    assert ok.json()["title"] == "Agora sim"
    assert ok.json()["owned_elsewhere"] is False


def test_apontar_melhor_para_onde_ele_mora_continua_permitido(client):
    """Corrigir a chave externa ou o link do Confluence não é divergir do
    original — é apontar melhor para ele."""
    story = _story(client)
    client.put(f"/api/v1/integrations/links/requirement/{story}",
               json={"system": "businessmap", "id": "CARD-77"})

    ok = client.put(f"/api/v1/requirements/{story}",
                    json={"confluence_url": "https://wiki/extrato"})
    assert ok.status_code == 200
    assert ok.json()["confluence_url"] == "https://wiki/extrato"


def test_requisito_local_continua_editavel(client):
    """A regra nova não pode atrapalhar quem escreve requisito aqui."""
    story = _story(client)
    r = client.put(f"/api/v1/requirements/{story}", json={"title": "Editado"})
    assert r.status_code == 200
    assert r.json()["title"] == "Editado"


# -- story sem epic também tem cobertura -------------------------------------


def test_story_sem_epic_nao_e_dada_como_descoberta(client):
    """Defeito encontrado medindo a tela (change 0158): a matriz era montada
    epic → stories, e a story órfã simplesmente não aparecia. A tela então a
    mostrava como "sem cobertura" mesmo coberta — e cobertura FALSA é pior do
    que cobertura ausente, porque alguém age sobre um buraco que não existe.
    """
    story = _story(client)  # nasce sem epic
    ct = _caso(client, story, ["EARS-1"])
    execucao = client.post("/api/v1/executions", json={
        "name": "Ciclo", "owner": "qa", "testcase_ids": [ct]}).json()["id"]
    client.post(f"/api/v1/executions/{execucao}/results/{ct}/status",
                json={"status": "passed"})

    matriz = client.get("/api/v1/metrics/traceability").json()
    nos_epics = [s for e in matriz["epics"] for s in e["stories"]
                 if s["id"] == story]
    assert nos_epics == []  # ela não pertence a epic nenhum, e tudo bem

    orfas = {s["id"]: s for s in matriz["orphan_stories"]}
    assert story in orfas
    assert orfas[story]["coverage_state"] == "passing"
    assert orfas[story]["ct_count"] == 1
    assert orfas[story]["criteria_covered"] == 1


def test_story_com_epic_inexistente_tambem_conta_como_orfa(client):
    """Epic apagado depois não pode fazer a story sumir da cobertura."""
    epic = client.post("/api/v1/requirements", json={
        "kind": "epic", "title": "Some depois"}).json()["id"]
    story = client.post("/api/v1/requirements", json={
        "kind": "story", "title": "Fica órfã", "epic": epic,
        "body": CORPO_STORY}).json()["id"]
    client.delete(f"/api/v1/requirements/{epic}")

    matriz = client.get("/api/v1/metrics/traceability").json()
    assert story in {s["id"] for s in matriz["orphan_stories"]}


def test_filtro_por_epic_nao_traz_orfas(client):
    """Pedir um epic específico é pedir aquele epic — anexar as órfãs ali
    seria responder outra pergunta."""
    epic = client.post("/api/v1/requirements", json={
        "kind": "epic", "title": "Um epic"}).json()["id"]
    _story(client)  # órfã

    matriz = client.get("/api/v1/metrics/traceability",
                        params={"epic": epic}).json()
    assert matriz["orphan_stories"] == []
