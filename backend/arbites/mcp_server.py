"""Servidor MCP do Arbites (change 0146, ADR 0015).

Processo LOCAL que fala MCP por stdio com o agente e HTTP com a instância do
Arbites. Não é um segundo backend: ele não abre banco, não lê o workspace e
não tem caminho privilegiado nenhum — toda resposta vem de uma rota da API,
autenticada pela credencial do agente. Por isso papel, módulo desligado e log
de atividade valem de graça (ADR 0014): o agente entra pela mesma porta que
o navegador.

## A regra de desenho

Expor o que o agente NÃO consegue calcular sozinho. Um espelho fino da REST
não agrega: o agente já sabe chamar HTTP e já sabe ler arquivo. O que ele não
tem é a resposta DERIVADA — quais critérios EARS estão sem caso, quais casos
um diff toca, o que ainda não foi sincronizado.

## Uso

    ARBITES_URL=http://192.168.0.17:8347 \\
    ARBITES_TOKEN=arb_... \\
    python -m arbites.mcp
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

API = "/api/v1"

SOMENTE_LEITURA = ToolAnnotations(readOnlyHint=True)

INSTRUCOES = """\
Arbites — plataforma local de gestão e rastreabilidade de testes.

Estas ferramentas respondem o que NÃO se descobre lendo o repositório: onde
falta cobertura (inclusive por critério EARS), quais casos um diff afeta, e o
que já está ligado a um sistema externo.

Regras que valem para todas:
- `by_tag` (vínculo explícito) e `by_risk` (correlação) têm confianças
  diferentes e não devem ser somados.
- Um resultado com a chave `refused` significa que o servidor recusou — em
  geral porque o administrador desligou aquele módulo. Leia o motivo e pare;
  repetir não muda a resposta.
"""


class McpRecusado(Exception):
    """O servidor recusou — e o motivo dele é o que o agente precisa ler."""


class ArbitesClient:
    """HTTP contra a instância, com a credencial do agente no Bearer."""

    def __init__(self, base: str, token: str) -> None:
        self.base = base.rstrip("/")
        self.token = token

    async def get(self, path: str, **params: Any) -> Any:
        limpos = {k: v for k, v in params.items() if v not in ("", None)}
        url = f"{self.base}{API}{path}"
        if limpos:
            url += "?" + urlencode(limpos)
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(url, headers={"Authorization": f"Bearer {self.token}"})
        if r.status_code >= 400:
            try:
                erro = r.json()["error"]
                raise McpRecusado(f"{erro['code']}: {erro['message']}")
            except (KeyError, ValueError):
                raise McpRecusado(f"HTTP {r.status_code}: {r.text[:200]}")
        return r.json()


def build_server(cli: ArbitesClient) -> MCPServer:
    """Monta o servidor. Recebe o cliente para o teste poder injetar o seu."""
    server = MCPServer(name="arbites", instructions=INSTRUCOES, version="0.1.0")

    async def _ou_recusa(corpo):
        """Recusa do servidor é RESPOSTA, não exceção: o agente precisa ler
        "módulo desligado pelo administrador" e parar — não tentar de novo."""
        try:
            return await corpo()
        except McpRecusado as e:
            return {"refused": str(e)}

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "O que falta cobrir de teste, por story e POR CRITÉRIO EARS. "
            "Devolve a LISTA dos critérios descobertos, não só a contagem — "
            "um número diz que há buraco, a lista diz onde ele está."
        ),
    )
    async def coverage_gaps(epic: str = "", story: str = "", squad: str = "") -> dict:
        return await _ou_recusa(
            lambda: cli.get("/metrics/coverage-gaps", epic=epic, story=story, squad=squad)
        )

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "Quais casos de teste um conjunto de arquivos alterados afeta — "
            "feito para receber os arquivos de um diff de PR. `by_tag` é "
            "vínculo explícito por tag de cenário (fato); `by_risk` é "
            "correlação por mapa de risco (palpite útil). Não some os dois."
        ),
    )
    async def impact_of_files(files: list[str]) -> dict:
        return await _ou_recusa(
            lambda: cli.get("/testcases/impact", files=",".join(files))
        )

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "Casos marcados como precisando de re-execução: os passos mudaram "
            "depois do último resultado, então o verde que mostram é de outra "
            "versão do caso."
        ),
    )
    async def pending_rerun() -> dict:
        async def corpo():
            casos = await cli.get("/testcases", needs_rerun="true")
            return {"testcases": casos, "count": len(casos)}

        return await _ou_recusa(corpo)

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "Pacote de contexto de um escopo (requisitos + casos + defeitos) "
            "em Markdown. Exige escopo — epic, story ou squad: o workspace "
            "inteiro não cabe em janela nenhuma e não ajuda ninguém."
        ),
    )
    async def context_pack(epic: str = "", story: str = "", squad: str = "") -> dict:
        if not (epic or story or squad):
            return {
                "refused": "scope_required: informe epic, story ou squad — o"
                " pacote não exporta o workspace inteiro sem recorte"
            }
        return await _ou_recusa(
            lambda: cli.get("/context-pack", epic=epic, story=story, squad=squad)
        )

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "Relatório de um ciclo: resultado por caso, passos e evidências, "
            "com o progresso por coluna do quadro."
        ),
    )
    async def execution_report(execution_id: str) -> dict:
        return await _ou_recusa(
            lambda: cli.get("/executions/" + quote(execution_id))
        )

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "O que daqui já está ligado a um sistema externo. É a consulta que "
            "torna qualquer escrita idempotente: antes de criar lá, pergunte o "
            "que já existe. `linked=false` devolve o que ainda não foi ligado."
        ),
    )
    async def external_links(linked: bool | None = None) -> dict:
        async def corpo():
            casos = await cli.get("/testcases")
            ligados = [
                {"testcase_id": c["id"], "title": c.get("title"),
                 "external_key": c.get("external_key")}
                for c in casos
            ]
            if linked is True:
                ligados = [c for c in ligados if c["external_key"]]
            elif linked is False:
                ligados = [c for c in ligados if not c["external_key"]]
            return {"links": ligados, "count": len(ligados)}

        return await _ou_recusa(corpo)

    @server.resource(
        "arbites://testcase/{testcase_id}",
        description="O corpo BDD de um caso de teste, por ID.",
        mime_type="text/markdown",
    )
    async def testcase_resource(testcase_id: str) -> str:
        """Recurso por URI: o agente referencia sem recolar o corpo inteiro."""
        caso = await cli.get("/testcases/" + quote(testcase_id))
        return caso.get("body") or ""

    return server


def client_from_env() -> ArbitesClient:
    base = os.environ.get("ARBITES_URL", "http://127.0.0.1:8347")
    token = os.environ.get("ARBITES_TOKEN", "")
    if not token:
        raise SystemExit(
            "ARBITES_TOKEN não definido — gere a credencial do agente no"
            " Arbites, em IA → MCP, e ponha no env do cliente MCP."
        )
    return ArbitesClient(base, token)


async def main() -> None:
    await build_server(client_from_env()).run_stdio_async()
