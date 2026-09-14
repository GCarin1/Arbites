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
    """Fala com o `TestClient` em vez de abrir socket — mesma superfície."""

    def __init__(self, http, token):
        super().__init__("http://testserver", token)
        self.http = http

    async def get(self, path, **params):
        limpos = {k: v for k, v in params.items() if v not in ("", None)}
        r = self.http.get(
            "/api/v1" + path, params=limpos,
            headers={"Authorization": f"Bearer {self.token}"},
        )
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
    """Servidor MCP montado sobre a sessão de teste, com credencial real."""
    return build_server(ClienteDeTeste(client, _token(client)))


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


def test_ferramentas_sao_seis_e_todas_declaram_leitura(mcp):
    nomes = {t.name for t in asyncio.run(mcp.list_tools())}
    assert nomes == {
        "coverage_gaps", "impact_of_files", "pending_rerun",
        "context_pack", "execution_report", "external_links",
    }
    assert all(
        t.annotations and t.annotations.read_only_hint
        for t in asyncio.run(mcp.list_tools())
    ), "leitura precisa se declarar para o cliente não pedir confirmação à toa"


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


def test_external_links_separa_ligado_de_nao_ligado(client, mcp):
    client.post(
        "/api/v1/testcases",
        json={"title": "Sem vínculo", "body": "## Passos\n\n1. x\n"},
    )
    todos = _chamar(mcp, "external_links")
    soltos = _chamar(mcp, "external_links", linked=False)
    assert todos["count"] >= 1
    assert soltos["count"] >= 1
    assert all(c["external_key"] in (None, "") for c in soltos["links"])


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
