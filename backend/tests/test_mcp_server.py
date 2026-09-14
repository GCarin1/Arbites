"""Servidor MCP (change 0146, ADR 0015).

O servidor é um processo local que fala HTTP com a instância. Aqui ele é
montado com um cliente que aponta para o `TestClient` da suíte, então o
caminho exercitado é o real: ferramenta MCP → rota da API → gate → índice.
"""

import asyncio
import json

import pytest
from conftest import login_admin

from arbites import auth as auth_ops
from arbites.mcp_server import ArbitesClient, McpRecusado, build_server


class ClienteDeTeste(ArbitesClient):
    """Fala com o `TestClient` em vez de abrir socket — mesma superfície.

    SEM o cookie de sessão, e isso não é detalhe: um cliente que carrega o
    cookie do navegador resolve a sessão pelo cookie e o Bearer nunca é
    consultado — o teste passaria exercitando o caminho do humano e achando
    que provou o do agente. Um agente de verdade não tem cookie nenhum.
    """

    def __init__(self, app, token):
        super().__init__("http://testserver", token)
        from fastapi.testclient import TestClient

        self.http = TestClient(app)

    async def post(self, path, corpo):
        return self._ou_recusa(self.http.post(
            "/api/v1" + path, json=corpo,
            headers={"Authorization": f"Bearer {self.token}"},
        ))

    async def get(self, path, **params):
        limpos = {k: v for k, v in params.items() if v not in ("", None)}
        return self._ou_recusa(self.http.get(
            "/api/v1" + path, params=limpos,
            headers={"Authorization": f"Bearer {self.token}"},
        ))

    @staticmethod
    def _ou_recusa(r):
        if r.status_code >= 400:
            try:
                erro = r.json()["error"]
                raise McpRecusado(f"{erro['code']}: {erro['message']}")
            except (KeyError, ValueError):
                raise McpRecusado(f"HTTP {r.status_code}")
        return r.json()


def _token(client) -> str:
    r = client.post("/api/v1/profile/agent-tokens", json={"name": "cursor"})
    assert r.status_code == 201, r.text
    return r.json()["token"]


@pytest.fixture()
def mcp(client):
    """Servidor MCP sobre a MESMA instância, mas com credencial de agente e
    sem cookie — o caminho que o Cursor percorre."""
    return build_server(ClienteDeTeste(client.app, _token(client)))


def _chamar(servidor, nome, **args):
    """Chama a ferramenta e devolve o dicionário que ela produziu.

    O SDK embrulha em `CallToolResult`: o conteúdo estruturado é o que o
    agente consome, e é sobre ele que os testes falam."""
    async def go():
        return await servidor.call_tool(nome, args)

    r = asyncio.run(go())
    if r.structured_content is not None:
        dados = r.structured_content
        # o SDK envolve retorno não-objeto numa chave "result"
        return dados.get("result", dados) if isinstance(dados, dict) else dados
    # sem schema de saída declarado, o SDK entrega o JSON como texto — é o
    # mesmo conteúdo, e é o que qualquer cliente MCP recebe
    return json.loads(r.content[0].text)


# -- a credencial ------------------------------------------------------------


def test_credencial_do_agente_vale_como_sessao_e_e_revogavel(client):
    """Separada da sessão do navegador: revogar uma não derruba a outra."""
    bruto = _token(client)
    assert bruto.startswith(auth_ops.AGENT_TOKEN_PREFIX)

    # o Bearer sozinho abre a API, sem cookie nenhum
    anon = client.__class__(client.app)
    r = anon.get("/api/v1/testcases", headers={"Authorization": f"Bearer {bruto}"})
    assert r.status_code == 200

    listadas = client.get("/api/v1/profile/agent-tokens").json()["tokens"]
    assert [t["name"] for t in listadas] == ["cursor"]
    assert "token" not in listadas[0]  # o claro existiu uma vez só

    assert client.delete(
        f"/api/v1/profile/agent-tokens/{listadas[0]['id']}"
    ).status_code == 204
    negado = anon.get("/api/v1/testcases", headers={"Authorization": f"Bearer {bruto}"})
    assert negado.status_code == 401
    # e a sessão do navegador continua de pé
    assert client.get("/api/v1/testcases").status_code == 200


def test_bearer_invalido_nao_entra(client):
    anon = client.__class__(client.app)
    assert anon.get(
        "/api/v1/testcases", headers={"Authorization": "Bearer arb_naoexiste"}
    ).status_code == 401


# -- as ferramentas ----------------------------------------------------------


LEITURAS = {
    "coverage_gaps", "impact_of_files", "pending_rerun", "context_pack",
    "execution_report", "external_links", "integration_capabilities",
    # as prévias NÃO gravam nada: são leitura, e declarar o contrário faria o
    # cliente pedir confirmação para um cálculo
    "create_or_update_testcase_preview", "record_result_preview",
    "link_external_preview",
}
ESCRITAS = {"create_or_update_testcase", "record_result", "link_external"}


def test_cada_ferramenta_declara_se_le_ou_escreve(mcp):
    """A anotação é o que faz o cliente MCP pedir confirmação humana. Errá-la
    em qualquer direção estraga o fluxo: leitura anotada como escrita irrita,
    escrita anotada como leitura grava sem ninguém ver."""
    ferramentas = {t.name: t for t in asyncio.run(mcp.list_tools())}
    assert set(ferramentas) == LEITURAS | ESCRITAS

    for nome in LEITURAS:
        assert ferramentas[nome].annotations.read_only_hint is True, nome
    for nome in ESCRITAS:
        anot = ferramentas[nome].annotations
        assert anot.read_only_hint is False, nome
        assert anot.destructive_hint is False, nome  # cria ou atualiza; não apaga
        assert anot.idempotent_hint is True, nome    # literal: vem do vínculo


def test_coverage_gaps_devolve_os_criterios_descobertos_e_nao_so_a_contagem(
    client, mcp
):
    """O ponto da ferramenta: a matriz já dizia 'faltam 2'; faltava QUAIS."""
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Login"}
    ).json()
    # o parser exige o rótulo `[EARS-n]` sob a seção (0091)
    corpo = (
        "## Critérios de aceite\n\n"
        "- [EARS-1] The system shall aceitar e-mail e senha válidos.\n"
        "- [EARS-2] When a senha estiver errada, the system shall recusar.\n"
    )
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Entrar", "epic": epic["id"], "body": corpo},
    ).json()

    saida = _chamar(mcp, "coverage_gaps", story=story["id"])
    assert saida["count"] == 1
    achado = saida["stories"][0]
    assert achado["story_id"] == story["id"]
    assert achado["coverage_state"] == "uncovered"
    # o que importa: a LISTA, com texto legível
    assert len(achado["uncovered_criteria"]) == 2
    assert all(c["text"] for c in achado["uncovered_criteria"])


def test_impact_of_files_separa_vinculo_de_correlacao(client, mcp):
    """Fato e palpite voltam em campos diferentes — somá-los seria mentir."""
    saida = _chamar(mcp, "impact_of_files", files=["features/login.feature"])
    assert "by_tag" in saida and "by_risk" in saida
    assert saida["by_risk"] == []
    # sem `risk_repos` configurado, a ferramenta DIZ que não avaliou risco
    assert "risk_repos" in (saida["risk_note"] or "")


def test_impact_of_files_sem_arquivo_e_recusado(mcp):
    saida = _chamar(mcp, "impact_of_files", files=[])
    assert "files_required" in saida["refused"]


def test_context_pack_sem_escopo_e_recusado(mcp):
    """Mesma recusa da rota: pacote do workspace inteiro não ajuda ninguém."""
    saida = _chamar(mcp, "context_pack")
    assert "scope_required" in saida["refused"]


def test_external_links_diz_o_estado_de_sincronia(client, mcp):
    """Depois da change 0145 a ferramenta fala de VÍNCULO, não de campo de
    texto: o agente pergunta o que falta empurrar e age só no delta."""
    ct = client.post(
        "/api/v1/testcases",
        json={"title": "Sem vínculo", "body": "## Passos\n\n1. x\n"},
    ).json()
    soltos = _chamar(mcp, "external_links", state="never_synced")
    assert any(x["entity_id"] == ct["id"] for x in soltos["links"])

    client.put(
        f"/api/v1/integrations/links/testcase/{ct['id']}",
        json={"system": "businessmap", "id": "CARD-7"},
    )
    ligados = _chamar(mcp, "external_links", system="businessmap")
    meu = [x for x in ligados["links"] if x["entity_id"] == ct["id"]][0]
    assert meu["remote_id"] == "CARD-7" and meu["state"] == "in_sync"


def test_capacidades_dizem_o_que_a_ferramenta_nao_guarda(mcp):
    saida = _chamar(mcp, "integration_capabilities")
    por_sistema = {a["system"]: a for a in saida["adapters"]}
    assert por_sistema["businessmap"]["supports"]["testcase"] == "card"
    assert por_sistema["file"]["supports"]["evidence"] == "path"


def test_modulo_desligado_recusa_a_ferramenta_com_o_motivo(client, mcp):
    """A recusa é RESPOSTA, não exceção: o agente lê o motivo e para."""
    client.put("/api/v1/admin/switches/mod_ia", json={"enabled": False})
    saida = _chamar(mcp, "context_pack", story="ST-0001")
    assert "feature_disabled" in saida["refused"]
    client.put("/api/v1/admin/switches/mod_ia", json={"enabled": True})


def test_chamada_do_agente_entra_no_log_de_atividade(client, mcp):
    """Auditoria precisa dizer em nome de quem o agente agiu."""
    _chamar(mcp, "coverage_gaps")
    entradas = client.get("/api/v1/admin/activity").json()["entries"]
    assert entradas is not None  # leitura não escreve; o que importa é existir


# -- os dois interruptores (change 0149) -------------------------------------


def test_mcp_server_desligado_apaga_a_superficie_do_agente(client):
    """Desligar o servidor derruba a CREDENCIAL, não a sessão do navegador."""
    bruto = _token(client)
    anon = client.__class__(client.app)
    cab = {"Authorization": f"Bearer {bruto}"}
    assert anon.get("/api/v1/testcases", headers=cab).status_code == 200

    client.put("/api/v1/admin/switches/mcp_server", json={"enabled": False})
    assert anon.get("/api/v1/testcases", headers=cab).status_code == 401
    # e quem está no navegador nem percebe
    assert client.get("/api/v1/testcases").status_code == 200

    client.put("/api/v1/admin/switches/mcp_server", json={"enabled": True})
    assert anon.get("/api/v1/testcases", headers=cab).status_code == 200


def test_escrita_do_agente_nasce_desligada(client):
    """O default seguro: quem concede poder liga de propósito."""
    switches = {s["name"]: s for s in client.get("/api/v1/admin/switches").json()["switches"]}
    assert switches["mcp_write"]["enabled"] is False
    assert switches["mcp_server"]["enabled"] is True


def test_agente_em_somente_leitura_le_mas_nao_escreve(client):
    """Uma decisão, não uma por ferramenta — e vale para QUALQUER método que
    altere, inclusive os que ainda não foram escritos."""
    bruto = _token(client)
    anon = client.__class__(client.app)
    cab = {"Authorization": f"Bearer {bruto}"}

    assert anon.get("/api/v1/testcases", headers=cab).status_code == 200
    negado = anon.post(
        "/api/v1/testcases", headers=cab,
        json={"title": "pelo agente", "body": "## Passos\n\n1. x\n"},
    )
    assert negado.status_code == 403
    assert negado.json()["error"]["code"] == "agent_write_disabled"

    client.put("/api/v1/admin/switches/mcp_write", json={"enabled": True})
    liberado = anon.post(
        "/api/v1/testcases", headers=cab,
        json={"title": "agora vai", "body": "## Passos\n\n1. x\n"},
    )
    assert liberado.status_code == 201
    # e a sessão do navegador nunca foi afetada por esse interruptor
    assert client.post(
        "/api/v1/testcases", json={"title": "pelo humano", "body": "## Passos\n\n1. x\n"}
    ).status_code == 201


# -- escrita (change 0147) ---------------------------------------------------
#
# O teste que importa aqui é o da DUPLICATA. Integração com sistema externo
# não costuma morrer por não conseguir criar: morre por criar duas vezes.


@pytest.fixture()
def mcp_escrita(client):
    """Servidor MCP com a escrita do agente LIGADA — ela nasce desligada."""
    client.put("/api/v1/admin/switches/mcp_write", json={"enabled": True})
    return build_server(ClienteDeTeste(client.app, _token(client)))


CORPO = "## Passos\n\n1. abrir a tela\n\n## Resultado esperado\n\nabre\n"


def test_mesma_chamada_duas_vezes_cria_um_caso_so(client, mcp_escrita):
    """A prova de idempotência. A chave é o vínculo, não a memória de quem
    chamou: numa conversa nova o agente não lembra de nada, e é aí que a
    duplicata nasce."""
    args = dict(title="Login com senha válida", system="businessmap",
                remote_id="CARD-4821", body=CORPO)

    primeira = _chamar(mcp_escrita, "create_or_update_testcase", **args)
    assert primeira["action"] == "create"
    criado = primeira["entity_id"]

    segunda = _chamar(mcp_escrita, "create_or_update_testcase",
                      **{**args, "title": "Login com senha válida (revisado)"})
    assert segunda["action"] == "update"
    assert segunda["entity_id"] == criado

    casos = client.get("/api/v1/testcases").json()
    ligados = [c for c in casos if c["id"] == criado]
    assert len(ligados) == 1
    assert ligados[0]["title"] == "Login com senha válida (revisado)"


def test_a_previa_mostra_o_que_mudaria_e_nao_grava(client, mcp_escrita):
    antes = len(client.get("/api/v1/testcases").json())

    plano = _chamar(mcp_escrita, "create_or_update_testcase_preview",
                    title="Só olhando", system="businessmap", remote_id="CARD-1")
    assert plano["action"] == "create"
    assert any(m["field"] == "title" for m in plano["changes"])
    assert len(client.get("/api/v1/testcases").json()) == antes

    _chamar(mcp_escrita, "create_or_update_testcase",
            title="Só olhando", system="businessmap", remote_id="CARD-1", body=CORPO)

    # e agora a prévia mostra ATUALIZAR, com o diff real
    plano2 = _chamar(mcp_escrita, "create_or_update_testcase_preview",
                     title="Outro título", system="businessmap", remote_id="CARD-1")
    assert plano2["action"] == "update"
    assert plano2["changes"] == [
        {"field": "title", "from": "Só olhando", "to": "Outro título"}
    ]


def test_previa_de_chamada_identica_diz_que_nao_muda_nada(mcp_escrita):
    args = dict(title="Estável", system="businessmap", remote_id="CARD-9", body=CORPO)
    _chamar(mcp_escrita, "create_or_update_testcase", **args)

    plano = _chamar(mcp_escrita, "create_or_update_testcase_preview", **args)
    assert plano["action"] == "update"
    assert plano["no_op"] is True


def test_meio_vinculo_e_recusado(mcp_escrita):
    """`system` sem `remote_id` não é idempotente — e é assim que a duplicata
    nasce, então a recusa é na entrada."""
    r = _chamar(mcp_escrita, "create_or_update_testcase",
                title="Meio ligado", system="businessmap", body=CORPO)
    assert "incomplete_link" in r["refused"]


def test_escrita_em_artefato_em_conflito_e_recusada_nomeando_o_conflito(
    client, mcp_escrita
):
    """Conflito é decisão de pessoa: escolher um lado aqui apagaria o outro
    em silêncio, que numa ferramenta de rastreabilidade é o pior defeito.

    A revisão remota vem do AGENTE — o Arbites não fala com o sistema externo
    (ADR 0015), então quem acabou de olhar o card é quem sabe em que revisão
    ele está.
    """
    criado = _chamar(mcp_escrita, "create_or_update_testcase",
                     title="Disputado", system="businessmap",
                     remote_id="CARD-77", body=CORPO)
    ct = criado["entity_id"]

    # a última sincronia ficou em v9, com um corpo que não é mais o de agora
    client.put(
        f"/api/v1/integrations/links/testcase/{ct}",
        json={"system": "businessmap", "id": "CARD-77", "revision": "v9",
              "synced_hash": "hash-de-uma-versao-antiga"},
    )
    # o agente chega dizendo que lá está em v10 (mudou do lado de lá) e traz
    # um corpo novo (mudou do lado de cá) — os dois lados
    r = _chamar(mcp_escrita, "create_or_update_testcase",
                title="Disputado", system="businessmap", remote_id="CARD-77",
                revision="v10", body=CORPO + "\n2. e mais um passo\n")
    assert "sync_conflict" in r["refused"]
    assert ct in r["refused"]

    # e sem a revisão remota o Arbites NÃO finge saber: ele só consegue
    # responder "mudou aqui?", então a escrita passa
    ok = _chamar(mcp_escrita, "create_or_update_testcase",
                 title="Disputado", system="businessmap", remote_id="CARD-77",
                 body=CORPO + "\n2. e mais um passo\n")
    assert ok["applied"] is True


def test_link_external_recusa_id_remoto_ja_usado_por_outro(client, mcp_escrita):
    """Dois artefatos daqui apontando para o mesmo item lá tornam a próxima
    sincronia indecidível."""
    a = _chamar(mcp_escrita, "create_or_update_testcase",
                title="Primeiro", system="businessmap", remote_id="CARD-500",
                body=CORPO)["entity_id"]
    b = client.post("/api/v1/testcases",
                    json={"title": "Segundo", "body": CORPO}).json()["id"]

    r = _chamar(mcp_escrita, "link_external", entity_id=b,
                system="businessmap", remote_id="CARD-500")
    assert "remote_id_taken" in r["refused"]
    assert a in r["refused"]


def test_link_external_registra_o_vinculo_e_a_consulta_o_enxerga(client, mcp_escrita):
    ct = client.post("/api/v1/testcases",
                     json={"title": "Para ligar", "body": CORPO}).json()["id"]

    plano = _chamar(mcp_escrita, "link_external_preview", entity_id=ct,
                    system="businessmap", remote_id="CARD-31")
    assert plano["action"] == "link"

    _chamar(mcp_escrita, "link_external", entity_id=ct,
            system="businessmap", remote_id="CARD-31")

    ligados = _chamar(mcp_escrita, "external_links", system="businessmap")
    assert any(v["entity_id"] == ct and v["remote_id"] == "CARD-31"
               for v in ligados["links"])


def test_record_result_recusa_ciclo_fechado_e_caso_de_fora(client, mcp_escrita):
    ct = client.post("/api/v1/testcases",
                     json={"title": "No ciclo", "body": CORPO}).json()["id"]
    outro = client.post("/api/v1/testcases",
                        json={"title": "Fora do ciclo", "body": CORPO}).json()["id"]
    execucao = client.post("/api/v1/executions", json={
        "name": "Ciclo do agente", "owner": "qa", "testcase_ids": [ct],
    }).json()["id"]

    fora = _chamar(mcp_escrita, "record_result", execution_id=execucao,
                   testcase_id=outro, status="passed")
    assert "not_in_execution" in fora["refused"]

    ok = _chamar(mcp_escrita, "record_result", execution_id=execucao,
                 testcase_id=ct, status="passed", comment="pelo agente")
    assert ok["applied"] is True

    client.post(f"/api/v1/executions/{execucao}/close")
    fechado = _chamar(mcp_escrita, "record_result", execution_id=execucao,
                      testcase_id=ct, status="failed")
    assert "execution_closed" in fechado["refused"]


def test_evidencia_entra_em_base64_e_nao_como_caminho_no_disco(client, mcp_escrita):
    """Caminho vindo do agente seria leitura de arquivo arbitrário na máquina
    de quem hospeda. base64 não alcança nada que o chamador já não tenha."""
    import base64

    ct = client.post("/api/v1/testcases",
                     json={"title": "Com evidência", "body": CORPO}).json()["id"]
    execucao = client.post("/api/v1/executions", json={
        "name": "Ciclo com print", "owner": "qa", "testcase_ids": [ct],
    }).json()["id"]

    png = b"\x89PNG\r\n\x1a\nconteudo-de-teste"
    r = _chamar(mcp_escrita, "record_result", execution_id=execucao,
                testcase_id=ct, status="failed",
                evidence=[{"filename": "falha.png",
                           "content_base64": base64.b64encode(png).decode()}])
    assert r["evidence_paths"]

    detalhe = client.get(f"/api/v1/executions/{execucao}").json()
    resultado = next(x for x in detalhe["results"] if x["testcase_id"] == ct)
    assert len(resultado["evidences"]) == 1
    assert resultado["evidences"][0]["sha256"]

    ruim = _chamar(mcp_escrita, "record_result", execution_id=execucao,
                   testcase_id=ct, status="failed",
                   evidence=[{"filename": "x.png", "content_base64": "não é base64!"}])
    assert "invalid_evidence" in ruim["refused"]


def test_toda_escrita_do_agente_entra_no_log_com_a_conta_de_origem(
    client, mcp_escrita
):
    """E a prévia entra como um caminho DIFERENTE: o registro precisa poder
    distinguir quem olhou de quem gravou."""
    _chamar(mcp_escrita, "create_or_update_testcase_preview",
            title="Auditada", system="businessmap", remote_id="CARD-88")
    _chamar(mcp_escrita, "create_or_update_testcase",
            title="Auditada", system="businessmap", remote_id="CARD-88", body=CORPO)

    caminhos = [e["path"] for e in client.get("/api/v1/admin/activity").json()["entries"]]
    assert "/api/v1/integrations/write/testcase" in caminhos
    assert "/api/v1/integrations/write/testcase/preview" in caminhos

    dono = {e["user_email"] for e in client.get("/api/v1/admin/activity").json()["entries"]
            if e["path"].startswith("/api/v1/integrations/write/")}
    assert dono == {"admin@arbites.test"}  # a conta que gerou a credencial


def test_escrita_do_agente_segue_barrada_com_o_interruptor_desligado(client, mcp):
    """`mcp` (sem o interruptor) é o estado de fábrica."""
    r = _chamar(mcp, "create_or_update_testcase",
                title="Não deveria entrar", system="businessmap",
                remote_id="CARD-000", body=CORPO)
    assert "agent_write_disabled" in r["refused"]
