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
# Declarada como escrita para o cliente MCP pedir confirmação humana.
# `destructiveHint=False` porque nada aqui apaga: cria ou atualiza.
# `idempotentHint=True` é literal, não aspiracional — a idempotência vem do
# vínculo externo, então repetir a mesma chamada converge no mesmo artefato.
ESCRITA = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True,
)

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

Para as ferramentas que ESCREVEM (`create_or_update_testcase`, `record_result`,
`link_external`), o fluxo é sempre o mesmo e não tem atalho:

1. chame a versão `..._preview` PRIMEIRO;
2. mostre o plano à pessoa — o campo `action` diz se vai criar ou atualizar,
   e `changes` diz exatamente o que muda;
3. só depois da confirmação dela chame a ferramenta que grava.

Antes de criar qualquer coisa num sistema externo, chame `external_links` para
saber o que já existe. É essa consulta que impede a duplicata: sua memória não
sobrevive à troca de conversa, o vínculo sobrevive.
"""


class McpRecusado(Exception):
    """O servidor recusou — e o motivo dele é o que o agente precisa ler."""


class ArbitesClient:
    """HTTP contra a instância, com a credencial do agente no Bearer.

    `impedimento` guarda o motivo de este cliente não poder falar com nada —
    falta de token, tipicamente. Ele NÃO derruba o processo (change 0200):
    um servidor que morre no arranque vira "Connection closed" no cliente
    MCP, que é o pior erro possível porque não diz nada. Subindo, o motivo
    chega ao agente na primeira chamada, escrito por extenso.
    """

    def __init__(self, base: str, token: str,
                 impedimento: str | None = None) -> None:
        self.base = base.rstrip("/")
        self.token = token
        self.impedimento = impedimento

    async def post(self, path: str, corpo: dict[str, Any]) -> Any:
        if self.impedimento:
            raise McpRecusado(self.impedimento)
        return self._ler(await self._chamar(
            "POST", f"{self.base}{API}{path}", json=corpo))

    async def get(self, path: str, **params: Any) -> Any:
        if self.impedimento:
            raise McpRecusado(self.impedimento)
        limpos = {k: v for k, v in params.items() if v not in ("", None)}
        url = f"{self.base}{API}{path}"
        if limpos:
            url += "?" + urlencode(limpos)
        return self._ler(await self._chamar("GET", url))

    async def _chamar(self, metodo: str, url: str, **kwargs):
        """A queda de rede vira RECUSA legível, não exceção crua.

        Um `ConnectError` subindo daqui aparece no agente como um traceback
        de httpx, que não diz a coisa útil: a instância não está no ar, ou o
        endereço está errado.
        """
        cabecalhos = {"Authorization": f"Bearer {self.token}"}
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                return await c.request(metodo, url, headers=cabecalhos, **kwargs)
        except httpx.TransportError as e:
            raise McpRecusado(
                f"o Arbites não respondeu em {self.base} ({type(e).__name__})."
                " Confira se ele está rodando e se ARBITES_URL aponta para"
                " ele — de outra máquina, o endereço não pode ser 127.0.0.1."
            ) from e

    @staticmethod
    def _ler(r) -> Any:
        if r.status_code >= 400:
            # 401 sem corpo legível é o caso mais comum e o mais mudo: dizer
            # só "HTTP 401" manda a pessoa procurar no lugar errado.
            if r.status_code == 401:
                raise McpRecusado(
                    "a credencial do agente foi recusada (401). Gere outra em"
                    " IA → MCP e ponha em ARBITES_TOKEN; um token revogado ou"
                    " de outra instância responde exatamente assim.")
            if r.status_code == 403:
                raise McpRecusado(
                    "a instância recusou (403) — em geral o interruptor"
                    " `mcp_server` está desligado em Administração, ou a"
                    " conta do agente não tem o papel necessário.")
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
            "O que daqui já está ligado a um sistema externo, e em que estado "
            "de sincronia. É a consulta que torna qualquer escrita "
            "idempotente: antes de criar lá, pergunte o que já existe. "
            "`state` filtra — `local_changed` é o que falta empurrar, "
            "`never_synced` é o que nunca foi, `conflict` é o que mudou dos "
            "DOIS lados e precisa de uma pessoa."
        ),
    )
    async def external_links(system: str = "", state: str = "") -> dict:
        return await _ou_recusa(
            lambda: cli.get("/integrations/links", system=system, state=state)
        )

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "O que cada sistema externo consegue representar. Consulte ANTES "
            "de sincronizar: o Businessmap é um quadro Kanban e não tem caso "
            "de teste nem evidência como conceito nativo, e o que ele não "
            "guarda precisa ser dito antes, não descoberto depois."
        ),
    )
    async def integration_capabilities() -> dict:
        return await _ou_recusa(lambda: cli.get("/integrations/capabilities"))

    # -- escrita (change 0147) ----------------------------------------------
    #
    # Cada escrita é um PAR: a de prévia calcula e não grava; a outra grava.
    # O par existe para que a confirmação humana caia entre as duas — e para
    # que o log de atividade da instância registre as duas como caminhos
    # diferentes, distinguindo quem olhou de quem gravou.

    def _corpo_testcase(**campos) -> dict:
        return {k: v for k, v in campos.items() if v not in ("", None, [])}

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "O que `create_or_update_testcase` FARIA, sem gravar nada. "
            "`action` responde a pergunta que importa: `create` ou `update`. "
            "Se vier `update`, é porque já existe caso daqui ligado a esse "
            "`remote_id` — criar outro seria a duplicata. Chame isto SEMPRE "
            "antes de gravar, e mostre o resultado à pessoa."
        ),
    )
    async def create_or_update_testcase_preview(
        title: str, system: str = "", remote_id: str = "", body: str = "",
        type: str = "", priority: str = "", status: str = "", story: str = "",
        tags: list[str] | None = None, folder: str = "",
    ) -> dict:
        return await _ou_recusa(lambda: cli.post(
            "/integrations/write/testcase/preview",
            _corpo_testcase(title=title, system=system, remote_id=remote_id,
                            body=body, type=type, priority=priority,
                            status=status, story=story, tags=tags, folder=folder),
        ))

    @server.tool(
        annotations=ESCRITA,
        description=(
            "Grava o caso de teste. IDEMPOTENTE pelo vínculo externo: com o "
            "mesmo `system` + `remote_id`, a segunda chamada ATUALIZA o caso "
            "que já existe em vez de criar um segundo. Informe os dois juntos "
            "ou nenhum — meio vínculo não é idempotente e é assim que a "
            "duplicata nasce. Recusa se o caso mudou dos dois lados desde a "
            "última sincronia: conflito é decisão de pessoa. "
            "Chame o `_preview` antes e confirme com a pessoa."
        ),
    )
    async def create_or_update_testcase(
        title: str, system: str = "", remote_id: str = "", body: str = "",
        type: str = "", priority: str = "", status: str = "", story: str = "",
        tags: list[str] | None = None, folder: str = "", revision: str = "",
    ) -> dict:
        return await _ou_recusa(lambda: cli.post(
            "/integrations/write/testcase",
            _corpo_testcase(title=title, system=system, remote_id=remote_id,
                            body=body, type=type, priority=priority,
                            status=status, story=story, tags=tags,
                            folder=folder, revision=revision),
        ))

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description=(
            "O que `record_result` faria, sem gravar. Recusa cedo — e diz o "
            "motivo — se o ciclo está fechado ou se o caso não faz parte dele."
        ),
    )
    async def record_result_preview(
        execution_id: str, testcase_id: str, status: str, comment: str = "",
    ) -> dict:
        return await _ou_recusa(lambda: cli.post(
            "/integrations/write/result/preview",
            {"execution_id": execution_id, "testcase_id": testcase_id,
             "status": status, "comment": comment or None},
        ))

    @server.tool(
        annotations=ESCRITA,
        description=(
            "Registra o resultado de um caso num ciclo ABERTO, com passos e "
            "evidência. Evidência vai em base64 dentro de `evidence` "
            "(`filename` + `content_base64`), NÃO como caminho no disco: "
            "caminho daqui seria leitura de arquivo arbitrário no computador "
            "de quem hospeda. Ciclo fechado é recusado — resultado em ciclo "
            "fechado reescreve um retrato que já foi usado para decidir."
        ),
    )
    async def record_result(
        execution_id: str, testcase_id: str, status: str, comment: str = "",
        steps: dict[str, str] | None = None,
        evidence: list[dict[str, str]] | None = None,
    ) -> dict:
        return await _ou_recusa(lambda: cli.post(
            "/integrations/write/result",
            {"execution_id": execution_id, "testcase_id": testcase_id,
             "status": status, "comment": comment or None,
             "steps": steps or None, "evidence": evidence or None},
        ))

    @server.tool(
        annotations=SOMENTE_LEITURA,
        description="O que `link_external` faria, sem gravar.",
    )
    async def link_external_preview(
        entity_id: str, system: str, remote_id: str, kind: str = "testcase",
    ) -> dict:
        return await _ou_recusa(lambda: cli.post(
            "/integrations/write/link/preview",
            {"entity_id": entity_id, "system": system,
             "remote_id": remote_id, "kind": kind},
        ))

    @server.tool(
        annotations=ESCRITA,
        description=(
            "Registra que um artefato daqui é o mesmo item de lá — por "
            "exemplo CT-0007 ↔ CARD-4821 no businessmap. É a MAIS "
            "importante das escritas, e parece a menor: sem ela você não tem "
            "como saber, numa conversa nova, que já criou aquele card — e "
            "recria. Chame-a logo depois de criar algo no sistema externo, "
            "sempre. Recusa se o `remote_id` já pertence a outro artefato."
        ),
    )
    async def link_external(
        entity_id: str, system: str, remote_id: str, kind: str = "testcase",
        revision: str = "",
    ) -> dict:
        return await _ou_recusa(lambda: cli.post(
            "/integrations/write/link",
            {"entity_id": entity_id, "system": system, "remote_id": remote_id,
             "kind": kind, "revision": revision or None},
        ))

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


FALTA_TOKEN = (
    "ARBITES_TOKEN não está definido no ambiente deste servidor MCP. Gere a"
    " credencial do agente no Arbites, em IA → MCP, e ponha em `env` do"
    " cliente — no mesmo bloco onde está `command` e `args`."
)


def client_from_env() -> ArbitesClient:
    """Sempre devolve um cliente. NUNCA derruba o processo.

    Derrubar era o comportamento antigo, e ele produzia o pior desfecho
    possível: o cliente MCP mostra "Connection closed" e nada mais, porque a
    mensagem sai em stderr e a maioria dos clientes não o exibe. A pessoa
    fica com um erro genérico e nenhuma pista (change 0200).
    """
    base = os.environ.get("ARBITES_URL", "http://127.0.0.1:8347")
    token = os.environ.get("ARBITES_TOKEN", "")
    return ArbitesClient(base, token, None if token else FALTA_TOKEN)


async def diagnostico(url: str | None = None,
                      token_dado: str | None = None) -> list[str]:
    """Por que o servidor MCP não está servindo — dito em texto, não em
    protocolo. Existe porque "Connection closed" não é um diagnóstico.

    `url` e `token_dado` vêm da linha de comando porque o ambiente do
    TERMINAL não é o ambiente do servidor: o bloco `env` do `mcp.json` é
    entregue pelo cliente ao processo que ele lança, e não existe no
    PowerShell. Sem essa passagem, o diagnóstico rodado à mão sempre
    responderia "NAO DEFINIDO" e mandaria procurar um problema que não é o
    da vez (change 0201).
    """
    base = url or os.environ.get("ARBITES_URL", "http://127.0.0.1:8347")
    token = token_dado or os.environ.get("ARBITES_TOKEN", "")
    linhas = [
        "arbites.mcp — diagnóstico",
        f"  ARBITES_URL   = {base}",
        # O token NUNCA é impresso: comprimento basta para reconhecer "colei
        # errado", e este texto vai ser colado num chat.
        "  ARBITES_TOKEN = " + (f"definido, {len(token)} caracteres"
                                if token else "NAO DEFINIDO"),
    ]
    if token != token.strip():
        linhas.append("  ATENCAO: o token tem espaço ou quebra de linha nas"
                      " pontas.")
    if not token:
        linhas.append(f"  -> {FALTA_TOKEN}")
        linhas.append("")
        linhas.append("  ATENCAO, antes de sair procurando: o bloco `env` do"
                      " mcp.json NAO vale neste terminal.")
        linhas.append("  O cliente entrega aquelas variáveis ao processo que"
                      " ELE lança; aqui elas não existem.")
        linhas.append("  Para conferir o que você vai pôr no mcp.json, passe"
                      " na mão:")
        linhas.append("    python -m arbites.mcp --diagnostico"
                      " --url http://SEU-IP:8347 --token arb_...")
        linhas.append("  A credencial se gera na própria instância, na aba"
                      " IA → MCP — a mesma da linha acima.")
        return linhas
    cliente = ArbitesClient(base, token)
    try:
        await cliente.get("/testcases", limit=1)
        linhas.append("  conexão e credencial: OK — o servidor consegue ler a"
                      " instância.")
    except McpRecusado as e:
        linhas.append(f"  RECUSADO: {e}")
    except Exception as e:  # noqa: BLE001
        linhas.append(f"  FALHA INESPERADA: {type(e).__name__}: {e}")
    return linhas


async def main() -> None:
    await build_server(client_from_env()).run_stdio_async()
