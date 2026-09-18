"""O servidor MCP que morria calado (change 0200).

O cliente MCP mostrava `Connection closed` e nada mais. Esse erro não é um
diagnóstico — é o cliente dizendo que não sabe. E ele não sabia porque o
servidor levantava `SystemExit` no arranque: a mensagem saía em stderr, que a
maioria dos clientes não exibe, e o processo morria antes de dizer qualquer
coisa pelo canal que o cliente lê.

A regra que estes testes fixam: o servidor SOBE, e o motivo chega ao agente
escrito por extenso na primeira chamada.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from arbites.mcp_server import (
    FALTA_TOKEN, ArbitesClient, McpRecusado, client_from_env, diagnostico,
)


# --- o arranque -------------------------------------------------------------


def test_sem_token_o_servidor_nao_derruba_o_processo(monkeypatch):
    """Derrubar produzia "Connection closed", o pior erro possível: genérico
    e sem pista nenhuma."""
    monkeypatch.delenv("ARBITES_TOKEN", raising=False)

    cliente = client_from_env()   # não levanta

    assert cliente.impedimento == FALTA_TOKEN


def test_sem_token_o_motivo_chega_na_primeira_chamada(monkeypatch):
    monkeypatch.delenv("ARBITES_TOKEN", raising=False)
    cliente = client_from_env()

    with pytest.raises(McpRecusado) as erro:
        asyncio.run(cliente.get("/testcases"))

    assert "ARBITES_TOKEN" in str(erro.value)
    assert "IA → MCP" in str(erro.value)


def test_com_token_nao_ha_impedimento(monkeypatch):
    monkeypatch.setenv("ARBITES_TOKEN", "arb_qualquer")

    assert client_from_env().impedimento is None


# --- os quatro modos de falhar ---------------------------------------------


class _Resposta:
    def __init__(self, status, corpo=None, texto=""):
        self.status_code, self._corpo, self.text = status, corpo, texto

    def json(self):
        if self._corpo is None:
            raise ValueError("sem json")
        return self._corpo


@pytest.mark.parametrize("status,marca", [
    (401, "credencial do agente foi recusada"),
    (403, "mcp_server"),
])
def test_recusa_da_instancia_e_dita_por_extenso(status, marca):
    """"HTTP 401" manda a pessoa procurar no lugar errado."""
    with pytest.raises(McpRecusado) as erro:
        ArbitesClient._ler(_Resposta(status))

    assert marca in str(erro.value)


def test_erro_conhecido_da_api_mantem_a_mensagem_dela():
    with pytest.raises(McpRecusado) as erro:
        ArbitesClient._ler(_Resposta(
            409, {"error": {"code": "agent_write_disabled",
                            "message": "escrita do agente desligada"}}))

    assert "agent_write_disabled" in str(erro.value)


def test_instancia_fora_do_ar_vira_recusa_legivel(monkeypatch):
    """Um `ConnectError` cru aparece no agente como traceback de httpx, que
    não diz a coisa útil: a instância não está no ar."""
    async def explode(*a, **k):
        raise httpx.ConnectError("recusou")

    monkeypatch.setattr(httpx.AsyncClient, "request", explode)
    cliente = ArbitesClient("http://127.0.0.1:9", "arb_x")

    with pytest.raises(McpRecusado) as erro:
        asyncio.run(cliente.get("/testcases"))

    assert "não respondeu" in str(erro.value)
    assert "127.0.0.1" in str(erro.value)


# --- o diagnóstico ----------------------------------------------------------


def test_o_diagnostico_diz_o_que_falta(monkeypatch):
    monkeypatch.delenv("ARBITES_TOKEN", raising=False)
    monkeypatch.setenv("ARBITES_URL", "http://exemplo:8347")

    saida = "\n".join(asyncio.run(diagnostico()))

    assert "http://exemplo:8347" in saida
    assert "NAO DEFINIDO" in saida


def test_o_diagnostico_nunca_imprime_o_token(monkeypatch):
    """Este texto existe para ser colado num chat."""
    segredo = "arb_segredo_que_nao_pode_vazar"
    monkeypatch.setenv("ARBITES_TOKEN", segredo)

    async def explode(*a, **k):
        raise httpx.ConnectError("recusou")

    monkeypatch.setattr(httpx.AsyncClient, "request", explode)
    saida = "\n".join(asyncio.run(diagnostico()))

    assert segredo not in saida
    # O comprimento SIM: é o que deixa reconhecer "colei metade do token".
    assert f"{len(segredo)} caracteres" in saida


def test_token_com_espaco_nas_pontas_e_denunciado(monkeypatch):
    monkeypatch.setenv("ARBITES_TOKEN", "arb_valido ")

    async def explode(*a, **k):
        raise httpx.ConnectError("recusou")

    monkeypatch.setattr(httpx.AsyncClient, "request", explode)
    saida = "\n".join(asyncio.run(diagnostico()))

    assert "espaço ou quebra de linha" in saida


# --- o ambiente do terminal NAO e o do servidor -----------------------------


def test_o_diagnostico_aceita_url_e_token_na_mao(monkeypatch):
    """O bloco `env` do mcp.json é entregue pelo cliente ao processo que ELE
    lança — no PowerShell aquelas variáveis não existem. Sem poder passá-las
    na mão, o diagnóstico rodado à mão responderia sempre "NAO DEFINIDO" e
    mandaria procurar o problema errado."""
    monkeypatch.delenv("ARBITES_TOKEN", raising=False)
    monkeypatch.delenv("ARBITES_URL", raising=False)

    async def explode(*a, **k):
        raise httpx.ConnectError("recusou")

    monkeypatch.setattr(httpx.AsyncClient, "request", explode)
    passado = "arb_passado_na_mao"
    saida = "\n".join(asyncio.run(diagnostico("http://outro:9000", passado)))

    assert "http://outro:9000" in saida
    assert f"{len(passado)} caracteres" in saida
    assert passado not in saida


def test_sem_token_o_diagnostico_avisa_que_o_env_do_mcp_nao_vale_aqui(monkeypatch):
    """A armadilha que este aviso evita: rodar no terminal, ler "NAO
    DEFINIDO" e concluir que o mcp.json está errado quando ele podia estar
    certo."""
    monkeypatch.delenv("ARBITES_TOKEN", raising=False)

    saida = "\n".join(asyncio.run(diagnostico()))

    assert "NAO vale neste terminal" in saida
    assert "--token" in saida


def test_as_duas_mensagens_apontam_o_MESMO_lugar(monkeypatch):
    """Duas instruções discordando sobre onde gerar a credencial mandam a
    pessoa para a tela errada — e ela conclui que a funcionalidade não
    existe."""
    monkeypatch.delenv("ARBITES_TOKEN", raising=False)

    saida = "\n".join(asyncio.run(diagnostico()))

    assert saida.count("IA → MCP") >= 2
    assert "Perfil →" not in saida
