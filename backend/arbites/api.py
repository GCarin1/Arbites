"""API REST do Arbites — M0.

Base: /api/v1. Erros no formato { "error": { "code", "message" } }.
Toda resposta de escrita retorna a entidade atualizada (contrato http-api).
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
import os
import re
import sqlite3
import zipfile
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

import frontmatter
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from . import agent_pack as agent_pack_ops
from . import integrations as integ_ops
from . import auth as auth_ops
from . import audit as audit_ops
from . import context_pack as context_pack_ops
from . import executions as exec_ops
from . import versioning
from . import project_memory as memory_ops
from . import risk_map as risk_map_ops
from . import metrics as metrics_ops
from . import ai as ai_ops
from . import daily as daily_ops
from . import xray_import as xray_ops
from .ai import AIKeyStore, AIProviderError
from . import build_front, ci_analise, ci_ingest
from . import tls as tls_ops
from . import versao as versao_ops, ci_retencao, integrations_bulk as bulk_ops
from . import notifications as notif_ops
from . import todolists as list_ops
from . import integrations_file as file_ops, mcp_write
from .ci import CIError, CIManager, HttpxGitHub, TokenStore
from .ci_credential import CredentialState
from .integrations_bulk import LoteErro
from .todolists import ListaErro
from .integrations_file import ArquivoErro
from .mcp_write import WriteRecusada
from .ci_ingest import CIIngestor, IngestError
from .executions import ExecutionError
from . import feature_sync as feature_sync_ops
from .gherkin_scan import (
    DEFAULT_FEATURES_GLOB,
    ct_tag_re,
    list_feature_files,
    scan_target,
)
from .runner import PythonPathError, RunManager, resolver_python
from .xray_import import XrayImportError
from .indexer import clear_needs_rerun, connect, reindex_file, reindex_full
from .parser import parse_markdown
from .watcher import start_watcher
from .workspace import Workspace, slugify

API_PREFIX = "/api/v1"

# Silencio maximo no stream de um run antes de emitir um comentario de
# keepalive. Bem abaixo do timeout de conexao ociosa do Cloudflare (~100s).
SSE_KEEPALIVE_SECONDS = 15.0
log = logging.getLogger("arbites")


# ---------------------------------------------------------------------------
# Modelos


class RequirementIn(BaseModel):
    kind: str = Field(pattern="^(epic|story)$")
    title: str
    status: str = "active"
    epic: str | None = None
    external_key: str | None = None
    confluence_url: str | None = None
    tags: list[str] = []
    squad: str | None = None
    body: str = ""


class RequirementUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    epic: str | None = None
    external_key: str | None = None
    confluence_url: str | None = None
    tags: list[str] | None = None
    squad: str | None = None
    body: str | None = None


class AutomationRef(BaseModel):
    target: str
    # vínculo por TAG no .feature (ADR 0003)…
    scenario_tag: str | None = None
    # …ou por NOME de cenário (mudança 0075; repo de automação read-only)
    feature_path: str | None = None
    scenario_name: str | None = None


class TestcaseIn(BaseModel):
    title: str
    type: str = Field(default="manual", pattern="^(manual|automated|hybrid)$")
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    status: str = Field(default="draft", pattern="^(draft|ready|deprecated)$")
    tags: list[str] = []
    story: str | None = None
    squad: str | None = None
    folder: str = ""
    automation: AutomationRef | None = None
    criteria: list[str] | None = None
    body: str | None = None


class TestcaseUpdate(BaseModel):
    title: str | None = None
    type: str | None = None
    priority: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    story: str | None = None
    squad: str | None = None
    automation: AutomationRef | None = None
    criteria: list[str] | None = None
    quarantine: bool | None = None
    body: str | None = None


class RawIn(BaseModel):
    content: str


class FolderIn(BaseModel):
    path: str  # relativo a <área>/, ex.: "frontend/login"


class FolderMoveIn(BaseModel):
    path: str  # pasta de origem, relativa a <área>/
    dest: str = ""  # pasta de destino, relativa a <área>/ (vazio = raiz)


class MoveIn(BaseModel):
    folder: str = ""  # destino relativo (vazio = raiz)


class ExternalLinkIn(BaseModel):
    """Vínculo com um sistema externo (change 0145)."""

    model_config = ConfigDict(extra="forbid")
    system: str
    id: str
    revision: str | None = None
    # quando ausente, o servidor carimba o hash do conteúdo ATUAL: é o caso
    # normal — quem acabou de sincronizar mandou o que está aqui agora
    synced_hash: str | None = None


class AgentTokenIn(BaseModel):
    """Credencial do agente MCP (change 0146). No módulo e não dentro da
    fábrica de rotas: com `from __future__ import annotations` as anotações
    viram string, e o FastAPI só resolve o nome nos globais — declarada
    local, ela vira parâmetro de QUERY em vez de corpo."""

    model_config = ConfigDict(extra="forbid")
    name: str


class ExecutionCreate(BaseModel):
    name: str
    sprint: str | None = None
    environment: str | None = None
    squad: str | None = None
    # O ciclo e a execution (ADR 0013): o periodo mora aqui, opcional.
    starts_on: str | None = None
    ends_on: str | None = None
    testcase_ids: list[str]
    # Mantido por compatibilidade de contrato; o valor e ignorado — a
    # autoria vem da sessao (capability profile).
    owner: str = "local"


class ExecutionPatch(BaseModel):
    name: str | None = None
    sprint: str | None = None
    environment: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|in_progress)$")
    starts_on: str | None = None
    ends_on: str | None = None


class AssigneeIn(BaseModel):
    # Vazio limpa o responsavel: o caso volta a ser de quem pegar.
    assignee: str | None = None


# `who` NAO entra por estes modelos (change 0115): a autoria vem da sessao,
# como o author_of() diz. `extra="forbid"` faz o cliente que insiste receber
# 422 em vez de mandar um campo que o servidor ignora em silencio.
class ResultStatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    comment: str | None = None
    column: str | None = None


class StepStatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str


class DefectLinkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    defect_id: str


class LocalRunIn(BaseModel):
    target: str
    tags: list[str] = []
    testcase_ids: list[str] = []
    feature: str | None = None  # .feature específico (behave <arquivo> --tags=)
    # 1..N arquivos .feature (mudança 0076) — todos entram como posicionais
    # do behave e a execution inclui os CTs lastreados de todos eles
    features: list[str] = []


class CIRunIn(BaseModel):
    target: str
    ref: str | None = None
    tags: list[str] = []
    testcase_ids: list[str] = []
    feature: str | None = None
    environment: str | None = None  # dev | cer | prd
    browser: str | None = None  # chrome (padrão CI)
    source_repo: str | None = None  # repositório que disparou


class EnvIn(BaseModel):
    values: dict[str, str] = {}


class ProfileIn(BaseModel):
    name: str | None = None
    memory: str | None = None


PROFILE_TEMPLATE = """## Preferências & Estilo

<!-- Como você prefere que a IA interaja: tom, formato de resposta,
tecnologias utilizadas, convenções do seu time. -->

-

## Contexto Ativo

<!-- O que está em andamento: projetos, decisões recentes, informações
relevantes. Mantenha vivo — remova o que ficou desatualizado. -->

-
"""


class McpTestcaseIn(BaseModel):
    """Escrita de caso vinda do agente. `system` + `remote_id` são o que
    tornam a chamada idempotente: com eles, repetir ATUALIZA."""
    title: str
    system: str | None = None
    remote_id: str | None = None
    revision: str | None = None
    type: str | None = None
    priority: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    story: str | None = None
    squad: str | None = None
    folder: str | None = None
    body: str | None = None


class McpEvidenceIn(BaseModel):
    filename: str
    content_base64: str
    mime: str | None = None
    note: str | None = None


class McpResultIn(BaseModel):
    execution_id: str
    testcase_id: str
    status: str
    comment: str | None = None
    steps: dict[str, str] | None = None
    evidence: list[McpEvidenceIn] | None = None


class NotificationIdsIn(BaseModel):
    ids: list[str] = []


class FileImportIn(BaseModel):
    """Importação por arquivo: o conteúdo vem no corpo, não como upload, para
    o agente MCP poder usar a mesma rota que a tela."""
    content: str
    system: str = "file"


class McpLinkIn(BaseModel):
    entity_id: str
    system: str
    remote_id: str
    kind: str = "testcase"
    revision: str | None = None


class TokenIn(BaseModel):
    token: str
    # Validade informada por quem criou o token: o provedor não conta ao
    # cliente quando o token expira (change 0157). Opcional — quem usa um
    # classic sem expiração simplesmente não informa.
    expires_at: str | None = None


class AIProviderConfig(BaseModel):
    name: str
    kind: str = "openai_compatible"
    model: str = ""
    base_url: str | None = None


class AIProvidersIn(BaseModel):
    default_provider: str | None = None
    providers: list[AIProviderConfig] = []
    keys: dict[str, str] = {}  # name → chave; vai direto ao keyring


class AnaliseCIIn(BaseModel):
    days: int = 30
    provider: str | None = None


class CompararAnalisesIn(BaseModel):
    a: str
    b: str
    provider: str | None = None


class ObservabilitySourceIn(BaseModel):
    """Um repositório de onde a observabilidade puxa execuções (change 0173).

    `workflow` e `artifact` vazios significam "todos" — é o caso comum e
    exigir os dois só faria o operador adivinhar nomes.
    """

    provider: str = "github"
    repo: str
    workflow: str | None = None
    artifact: str | None = None


class ObservabilitySourcesIn(BaseModel):
    sources: list[ObservabilitySourceIn] = []
    max_runs_per_poll: int | None = None


class GithubTargetIn(BaseModel):
    """Onde o workflow deste alvo mora. Sem `repo` e `workflow` o dispatch
    não tem para onde ir — e este bloco não tinha representação no modelo,
    então salvar o alvo pela tela APAGAVA o que estivesse escrito à mão no
    `arbites.yaml` (change 0172)."""

    repo: str = ""       # "owner/repo"
    workflow: str = ""   # nome do arquivo, ex.: "e2e.yml"
    ref: str | None = None


class AutomationTargetIn(BaseModel):
    name: str
    kind: str = "behave"
    local_path: str
    features_glob: str = DEFAULT_FEATURES_GLOB
    python_path: str | None = None
    working_dir: str | None = None
    timeout_minutes: float | None = None
    github: GithubTargetIn | None = None


class AutomationTargetsIn(BaseModel):
    targets: list[AutomationTargetIn] = []


class FeatureSyncItem(BaseModel):
    feature_path: str
    scenario_name: str


class FeatureSyncRelink(BaseModel):
    ct_id: str
    feature_path: str
    scenario_name: str


class FeatureSyncApplyIn(BaseModel):
    target: str
    create: list[FeatureSyncItem] = []
    update: list[str] = []  # ct_ids com steps modificados → re-basear body
    relink: list[FeatureSyncRelink] = []
    folder: str | None = None  # pasta dos CTs criados (default automacao/<target>)


class GenerateIn(BaseModel):
    source: str  # story_id (ST-XXXX) ou texto/markdown livre
    provider: str | None = None  # default_provider se omitido
    criteria: list[str] | None = None  # gerar POR critério EARS (0093)


class AIByCtIn(BaseModel):
    provider: str | None = None


class ProviderTestIn(BaseModel):
    # testa um provider SALVO (name) ou uma config INLINE ainda não salva (0085)
    name: str | None = None
    kind: str | None = None
    model: str | None = None
    base_url: str | None = None
    key: str | None = None


class _InlineKeys:
    """Keystore efêmero: devolve a chave inline para o provider em teste,
    delegando o resto ao keystore real (0085)."""

    def __init__(self, base, name: str, key: str):
        self._base, self._name, self._key = base, name, key

    def get(self, name: str):
        return self._key if name == self._name else self._base.get(name)

    def configured(self, name: str) -> bool:
        return True if name == self._name else self._base.configured(name)


class DefectIn(BaseModel):
    title: str
    severity: str = "medium"
    status: str = Field(default="open", pattern="^(open|fixed|closed)$")
    testcase: str | None = None
    execution: str | None = None
    external_key: str | None = None
    body: str = ""
    # Banco de Lições Aprendidas (doc de ideias): causa raiz + correção +
    # prevenção — a IA cruza isto ao gerar CTs pra não repetir o mesmo bug.
    root_cause: str | None = None
    fix: str | None = None
    prevention: str | None = None
    # Lição estruturada (0095): when/procedure/anti-pattern — preferida na
    # injeção de IA e vira skill no Pacote de Agente.
    lesson_when: str | None = None
    lesson_procedure: str | None = None
    lesson_antipattern: str | None = None


class DefectUpdate(BaseModel):
    title: str | None = None
    severity: str | None = None
    status: str | None = None
    testcase: str | None = None
    execution: str | None = None
    external_key: str | None = None
    body: str | None = None
    root_cause: str | None = None
    fix: str | None = None
    prevention: str | None = None
    lesson_when: str | None = None
    lesson_procedure: str | None = None
    lesson_antipattern: str | None = None


class TodoIn(BaseModel):
    title: str
    status: str = Field(default="open", pattern="^(open|doing|blocked|done)$")
    due: str | None = None
    squad: str | None = None
    links: list[str] = []
    body: str = ""


class TodoUpdate(BaseModel):
    title: str | None = None
    status: str | None = Field(default=None, pattern="^(open|doing|blocked|done)$")
    due: str | None = None
    squad: str | None = None
    links: list[str] | None = None
    body: str | None = None


class TodoListIn(BaseModel):
    title: str
    due: str | None = None
    body: str = ""


class TodoListUpdate(BaseModel):
    title: str | None = None
    status: str | None = Field(default=None, pattern="^(active|done|archived)$")
    due: str | None = None
    body: str | None = None


class TodoListItemIn(BaseModel):
    text: str
    done: bool = False
    # O vínculo com o afazer mora AQUI, na linha, e só aqui (change 0164).
    todo: str | None = None


class TodoListItemUpdate(BaseModel):
    text: str | None = None
    done: bool | None = None
    todo: str | None = None


class DailyIn(BaseModel):
    body: str = ""
    action_items: list[str] = []


class DailyGenerateIn(BaseModel):
    provider: str | None = None


class MeetingIn(BaseModel):
    title: str
    date: str | None = None
    body: str = ""


class MeetingUpdate(BaseModel):
    title: str | None = None
    date: str | None = None
    summary: str | None = None
    body: str | None = None


class DecisionIn(BaseModel):
    title: str
    status: str = Field(default="proposed", pattern="^(proposed|accepted|superseded)$")
    squad: str | None = None
    tags: list[str] = []
    supersedes: str | None = None
    body: str | None = None


class DecisionUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    squad: str | None = None
    tags: list[str] | None = None
    supersedes: str | None = None
    body: str | None = None


class MeetingSummarizeIn(BaseModel):
    provider: str | None = None


class MeetingActionItemsGenerateIn(BaseModel):
    provider: str | None = None


class MeetingActionItemsAcceptIn(BaseModel):
    items: list[str]


class ExecutiveSummaryIn(BaseModel):
    provider: str | None = None
    sprint: str | None = None
    squad: str | None = None


# Catálogo do .env: DERIVADO do próprio projeto-alvo (0099). O Arbites se
# adapta a cada projeto — não impõe campos padrão de projeto nenhum. As chaves,
# seções e descrições vêm do `.env.example` (preferido, documenta tudo) e do
# `.env` do target. Regra de parse:
#   - `# Seção` seguido de linha em branco  → cabeçalho de seção
#   - `# descrição` logo acima de uma chave → descrição da chave
#   - `KEY=valor  # descrição inline`        → descrição (tem prioridade)
def derive_env_catalog(local_path: Path) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    seen: set[str] = set()
    for filename in (".env.example", ".env"):
        path = local_path / filename
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            continue
        section = ""
        pending_desc = ""
        for i, raw in enumerate(lines):
            stripped = raw.strip()
            if not stripped:
                pending_desc = ""
                continue
            if stripped.startswith("#"):
                comment = stripped.lstrip("#").strip(" =-")
                # comentário seguido de linha em branco → é seção
                nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if not nxt:
                    section = comment
                    pending_desc = ""
                else:
                    pending_desc = comment
                continue
            if "=" not in stripped:
                continue
            key_part, _, rest = stripped.partition("=")
            key = key_part.strip()
            if key.lower().startswith("export "):
                key = key[len("export "):].strip()
            if not key or key in seen:
                continue
            seen.add(key)
            inline = rest.split("#", 1)[1].strip() if "#" in rest else ""
            catalog.append({
                "section": section,
                "key": key,
                "description": inline or pending_desc,
            })
            pending_desc = ""
    return catalog

# Formato canônico BDD (doc de ajustes §1.1) — steps extraídos de Given/When/Then
DEFAULT_TC_BODY = """Feature: [Nome da Feature]

  Scenario: [Nome do Cenário]
    Given [pré-condição]
    When [ação executada]
    Then [resultado esperado]
"""

# Template leve (não é o ADR do Doctrina — é uma decisão do TIME DE QA sobre o
# projeto sob teste; "ponteiro + metadados", mesmo espírito de defects).
DEFAULT_DECISION_BODY = """## Contexto

[Por que esta decisão precisou ser tomada?]

## Decisão

[O que foi decidido?]

## Consequências

[O que isso implica pra frente — positivo e negativo?]
"""


# ---------------------------------------------------------------------------
# App factory


def create_app(
    workspace_root: str | os.PathLike[str] | None = None,
    watch: bool = True,
    github_client=None,
    token_store: TokenStore | None = None,
    ai_key_store: AIKeyStore | None = None,
    ai_transport=None,
    auth_enabled: bool | None = None,
) -> FastAPI:
    ws = Workspace(workspace_root or os.environ.get("ARBITES_WORKSPACE", "workspace"))
    if auth_enabled is None:
        auth_enabled = os.environ.get("ARBITES_AUTH", "on").strip().lower() != "off"
    tokens = token_store or TokenStore()
    github = github_client or HttpxGitHub(tokens)
    ai_keys = ai_key_store or AIKeyStore()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ws.ensure()
        app.state.ws = ws
        app.state.conn = connect(ws)
        app.state.conn.execute("PRAGMA busy_timeout=5000")
        reindex_full(ws, app.state.conn)
        app.state.runner = RunManager(ws, app.state.conn)
        app.state.tokens = tokens
        app.state.credential = CredentialState(ws)
        # O cliente real ganha memória da recusa; um fake de teste não tem o
        # atributo e segue como antes.
        if hasattr(github, "credential") and github.credential is None:
            github.credential = app.state.credential
        app.state.ci = CIManager(ws, app.state.conn, github, tokens)
        app.state.ci_ingest = CIIngestor(ws, app.state.conn, github)
        app.state.ai_keys = ai_keys
        app.state.ai_transport = ai_transport
        # Banco de contas: conexao propria e duravel, jamais a do indice
        # descartavel (ADR 0011).
        app.state.auth = auth_ops.connect_auth(ws)
        app.state.auth_enabled = auth_enabled
        if auth_enabled:
            created = auth_ops.bootstrap_admin(app.state.auth)
            if created is not None:
                log.warning(
                    "conta admin de bootstrap criada para %s — troque a senha"
                    " no primeiro login", created["email"],
                )
            elif auth_ops.count_active_admins(app.state.auth) == 0:
                # Antes isto era um no-op SILENCIOSO: a instância subia sem
                # conta nenhuma e a pessoa ia tentar entrar numa conta que
                # nunca existiu, até se trancar por tentativas (change 0165).
                # Um arranque que não pode dar certo precisa dizer isso.
                log.error(
                    "NENHUMA conta de administrador existe e o ambiente nao traz"
                    " credencial de bootstrap: ninguem consegue entrar. Defina"
                    " ARBITES_ADMIN_EMAIL e ARBITES_ADMIN_PASSWORD (a senha"
                    " precisa de %d caracteres ou mais) num arquivo .env no"
                    " diretorio onde voce roda o comando, ou no ambiente do"
                    " processo, e suba de novo.", auth_ops.MIN_PASSWORD_LEN,
                )
        else:
            log.warning(
                "ARBITES_AUTH=off — a API esta SEM autenticacao. Nao exponha"
                " esta instancia fora de uma rede confiavel.",
            )
        observer = None
        if watch:
            watch_conn = connect(ws)
            watch_conn.execute("PRAGMA busy_timeout=5000")
            observer = start_watcher(ws, watch_conn)
        yield
        await app.state.runner.shutdown()
        if observer is not None:
            observer.stop()
        app.state.conn.close()
        app.state.auth.close()

    app = FastAPI(title="Arbites", version=__version__, lifespan=lifespan)

    @app.exception_handler(HTTPException)
    async def _http_error(request: Request, exc: HTTPException):
        detail = exc.detail
        if not isinstance(detail, dict):
            detail = {"code": "error", "message": str(detail)}
        return JSONResponse(status_code=exc.status_code, content={"error": detail})

    @app.exception_handler(ExecutionError)
    async def _exec_error(request: Request, exc: ExecutionError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(XrayImportError)
    async def _xray_error(request: Request, exc: XrayImportError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def _falha_inesperada(request: Request, exc: Exception):
        """A rede de segurança: nenhuma exceção desconhecida vira traceback.

        O traceback continua indo para o LOG do servidor — é onde ele serve,
        para quem vai corrigir. O que muda é a resposta: quem clicou recebia
        500 com uma parede de stack trace e nenhuma instrução, e o motivo
        real ficava enterrado no meio (change 0185).

        A mensagem não repassa `str(exc)`: uma exceção qualquer pode carregar
        caminho de arquivo, trecho de SQL ou pedaço de credencial, e essa
        resposta sai para o navegador. O identificador amarra a resposta à
        linha do log, que tem tudo.
        """
        import traceback
        import uuid

        marca = uuid.uuid4().hex[:8]
        print(f"[arbites:{marca}] falha não tratada em"
              f" {request.method} {request.url.path}")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return JSONResponse(
            status_code=500,
            content={"error": {
                "code": "internal_error",
                "message": ("falha inesperada no servidor. O detalhe está no"
                            f" log do terminal, marcado como [arbites:{marca}]."),
                "trace_id": marca,
            }},
        )

    @app.exception_handler(CIError)
    async def _ci_error(request: Request, exc: CIError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(ListaErro)
    async def _lista_erro(request: Request, exc: ListaErro):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(LoteErro)
    async def _lote_erro(request: Request, exc: LoteErro):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(ArquivoErro)
    async def _arquivo_erro(request: Request, exc: ArquivoErro):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(WriteRecusada)
    async def _write_recusada(request: Request, exc: WriteRecusada):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(IngestError)
    async def _ingest_error(request: Request, exc: IngestError):
        status = {"no_sources": 409, "not_found": 404}.get(exc.code, 422)
        return JSONResponse(
            status_code=status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(AIProviderError)
    async def _ai_error(request: Request, exc: AIProviderError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(auth_ops.AuthError)
    async def _auth_error(request: Request, exc: auth_ops.AuthError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    _register_auth(app)
    _register_routes(app)
    _mount_frontend(app)
    return app


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status, {"code": code, "message": message})


# ---------------------------------------------------------------------------
# Helpers de arquivo


def _write_doc(path: Path, meta: dict[str, Any], body: str) -> None:
    post = frontmatter.Post(body, **{k: v for k, v in meta.items() if v is not None})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


def _load_doc(ws: Workspace, rel: str) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(str(ws.root / rel))
    return dict(post.metadata), post.content


def _todos_markdown(items: list[dict]) -> str:
    lines = ["# Afazeres", "", f"Total: {len(items)}", ""]
    for t in items:
        lines.append(f"## {t['id']} — {t['title']}")
        meta = [f"status: {t['status']}"]
        if t.get("due"):
            meta.append(f"prazo: {t['due']}")
        if t.get("squad"):
            meta.append(f"squad: {t['squad']}")
        if t.get("links"):
            meta.append(f"links: {t['links']}")
        lines.append(" · ".join(meta))
        if (t.get("body") or "").strip():
            lines += ["", t["body"].strip()]
        lines.append("")
    return "\n".join(lines)


def _todos_xml(items: list[dict]) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<todos>"]
    for t in items:
        out.append(f'  <todo id="{_xml_escape(t["id"], {chr(34): "&quot;"})}">')
        out.append(f"    <title>{_xml_escape(t['title'] or '')}</title>")
        out.append(f"    <status>{_xml_escape(t['status'] or '')}</status>")
        out.append(f"    <due>{_xml_escape(t.get('due') or '')}</due>")
        out.append(f"    <squad>{_xml_escape(t.get('squad') or '')}</squad>")
        out.append(f"    <links>{_xml_escape(t.get('links') or '')}</links>")
        out.append(f"    <description>{_xml_escape((t.get('body') or '').strip())}</description>")
        out.append("  </todo>")
    out.append("</todos>")
    return "\n".join(out)


def _find_path(conn: sqlite3.Connection, table: str, entity_id: str) -> str:
    row = conn.execute(f"SELECT path FROM {table} WHERE id = ?", (entity_id,)).fetchone()
    if not row:
        raise _error(404, "not_found", f"{entity_id} não encontrado")
    return row["path"]


def _req_out(conn: sqlite3.Connection, ws: Workspace, entity_id: str) -> dict:
    row = conn.execute("SELECT * FROM requirements WHERE id = ?", (entity_id,)).fetchone()
    if not row:
        raise _error(404, "not_found", f"{entity_id} não encontrado")
    out = dict(row)
    out["tags"] = [t for t in (out.get("tags") or "").split(",") if t]
    meta, out["body"] = _load_doc(ws, row["path"])
    # A ORIGEM do requisito (change 0158). Requisito é insumo do time de
    # negócio: quando ele vive no sistema oficial, a cópia daqui é espelho, e
    # a tela precisa dizer isso antes de alguém editar e criar divergência.
    out["external"] = integ_ops.read_links(meta)
    out["owned_elsewhere"] = bool(out["external"])
    return out


def _tc_out(conn: sqlite3.Connection, ws: Workspace, entity_id: str) -> dict:
    row = conn.execute("SELECT * FROM testcases WHERE id = ?", (entity_id,)).fetchone()
    if not row:
        raise _error(404, "not_found", f"{entity_id} não encontrado")
    out = dict(row)
    out["quarantine"] = bool(row["quarantine"])
    out["needs_rerun"] = bool(row["needs_rerun"])
    out["tags"] = [
        r["tag"]
        for r in conn.execute(
            "SELECT tag FROM tc_tags WHERE testcase_id = ?", (entity_id,)
        )
    ]
    out["criteria"] = [
        r["ears_id"]
        for r in conn.execute(
            "SELECT ears_id FROM tc_criteria WHERE testcase_id = ? ORDER BY ears_id",
            (entity_id,),
        )
    ]
    _, out["body"] = _load_doc(ws, row["path"])
    return out


# ---------------------------------------------------------------------------
# Rotas


def author_of(request: Request) -> str:
    """Quem assina o que esta sendo escrito. Vem SEMPRE da sessao: aceitar
    autoria do corpo faria dela um campo que qualquer um preenche com o nome
    de qualquer um."""
    if not getattr(request.app.state, "auth_enabled", True):
        return "local"
    user = getattr(request.state, "user", None)
    return (user or {}).get("email", "local")


def _register_routes(app: FastAPI) -> None:
    def ws_of(request: Request) -> Workspace:
        return request.app.state.ws

    def conn_of(request: Request) -> sqlite3.Connection:
        return request.app.state.conn

    # -- workspace ------------------------------------------------------

    @app.get(API_PREFIX + "/workspace")
    async def get_workspace(request: Request):
        ws, conn = ws_of(request), conn_of(request)
        meta = {
            row["key"]: row["value"]
            for row in conn.execute("SELECT key, value FROM index_meta")
        }
        return {
            "config": ws.config(),
            "root": str(ws.root),
            "index": {
                "last_reindex": meta.get("last_reindex"),
                "last_reindex_seconds": meta.get("last_reindex_seconds"),
                "requirements": conn.execute(
                    "SELECT COUNT(*) c FROM requirements"
                ).fetchone()["c"],
                "testcases": conn.execute("SELECT COUNT(*) c FROM testcases").fetchone()["c"],
                "warnings": conn.execute("SELECT COUNT(*) c FROM warnings").fetchone()["c"],
            },
        }

    @app.post(API_PREFIX + "/workspace/reindex")
    async def post_reindex(request: Request):
        return reindex_full(ws_of(request), conn_of(request))

    def _avisos_compostos(request: Request) -> list[dict[str, Any]]:
        """Os problemas do índice MAIS os derivados da credencial.

        Uma função só porque o sino (change 0161) e a aba Problemas leem daqui:
        duas listas montadas em lugares diferentes divergiriam no primeiro
        aviso novo, e o sino passaria a mostrar coisa que a aba não mostra.
        """
        avisos = [
            dict(row)
            for row in conn_of(request).execute(
                "SELECT source_path, code, message, created_at FROM warnings"
                " ORDER BY source_path, code"
            )
        ]
        # O problema da credencial é DERIVADO a cada leitura, não guardado na
        # tabela acima: aquela tabela é do índice, e um reindex a esvazia — o
        # problema voltaria a ser invisível justamente no cenário que a change
        # 0157 existe para cobrir. Vem primeiro porque bloqueia a ingestão
        # inteira, enquanto um aviso de integridade é de um arquivo só.
        credencial: CredentialState = request.app.state.credential
        tokens = request.app.state.tokens
        # Build velho do frontend (change 0182): DERIVADO a cada leitura, como
        # o da credencial. A tela que mostra este aviso é a antiga — e é
        # justamente por isso que ela precisa mostrá-lo: a API está atual.
        do_build = build_front.aviso(_dist_do_frontend())
        # Bundle de CA quebrado (change 0186): aparece sem ninguém clicar em
        # nada. Uma configuração que não funciona só se revelava na primeira
        # chamada externa, e até lá parecia que estava tudo certo.
        do_ca = tls_ops.aviso()
        return credencial.problemas(
            tokens.get() is not None,
            gravavel=tokens.available(), origem=tokens.source(),
        ) + ([do_ca] if do_ca else []) + ([do_build] if do_build else []) + avisos

    @app.get(API_PREFIX + "/warnings")
    async def get_warnings(request: Request):
        return _avisos_compostos(request)

    # -- o sino (change 0161) -----------------------------------------------
    #
    # A lista é DERIVADA das fontes que já são verdade; o que se grava é só o
    # que cada pessoa leu e até onde limpou. Caixa de entrada gravada criaria
    # um segundo estado, e o segundo estado diverge: o aviso corrigido
    # continuaria na lista e alguém agiria sobre um buraco que não existe.

    @app.get(API_PREFIX + "/notifications")
    async def listar_notificacoes(request: Request, days: int = 14):
        usuario = current_user(request)
        com_log = (
            usuario.get("role") == "admin"
            and auth_ops.switch_enabled(request.app.state.auth, "notifications_info")
        )
        try:
            painel = ci_ingest.painel(ws_of(request), conn_of(request), days)
        except Exception:  # noqa: BLE001 — observabilidade é UMA fonte
            # Se ela falhar, o sino ainda serve as outras. Um sino que morre
            # inteiro porque uma fonte tropeçou é pior do que um sino parcial.
            painel = None
        return notif_ops.listar(
            conn_of(request), request.app.state.auth, usuario,
            _avisos_compostos(request), painel, com_log,
        )

    @app.post(API_PREFIX + "/notifications/{notification_id}/read")
    async def marcar_lida(request: Request, notification_id: str):
        notif_ops.marcar(request.app.state.auth, current_user(request)["id"],
                         notification_id, True)
        return {"id": notification_id, "read": True}

    @app.delete(API_PREFIX + "/notifications/{notification_id}/read")
    async def marcar_nao_lida(request: Request, notification_id: str):
        notif_ops.marcar(request.app.state.auth, current_user(request)["id"],
                         notification_id, False)
        return {"id": notification_id, "read": False}

    @app.post(API_PREFIX + "/notifications/read-all")
    async def marcar_todas_lidas(request: Request, payload: NotificationIdsIn):
        return {"marked": notif_ops.marcar_todas(
            request.app.state.auth, current_user(request)["id"], payload.ids)}

    @app.post(API_PREFIX + "/notifications/clear")
    async def limpar_notificacoes(request: Request):
        """Limpar é marca d'água, não DELETE: não há o que apagar, a lista é
        derivada. Grava-se "vi tudo até aqui"."""
        return {"cleared_at": notif_ops.limpar(
            request.app.state.auth, current_user(request)["id"])}

    # -- lixeira (0081) ---------------------------------------------------

    @app.get(API_PREFIX + "/trash")
    async def get_trash(request: Request):
        return ws_of(request).list_trash()

    @app.post(API_PREFIX + "/trash/{name}/restore")
    async def restore_trash(request: Request, name: str):
        ws, conn = ws_of(request), conn_of(request)
        try:
            restored = ws.restore(name)
        except FileNotFoundError:
            raise _error(404, "not_found", f"{name} não está na lixeira")
        # reindexa o que voltou: arquivo único ou todos os artefatos da pasta
        if restored.is_dir():
            for p in restored.rglob("*"):
                if p.suffix == ".md" or p.name == "execution.json":
                    reindex_file(ws, conn, p)
        else:
            reindex_file(ws, conn, restored)
        # Restaurar e o desfazer de uma exclusao que foi registrada: deixa-lo
        # de fora quebraria o par (change 0121). So casos de teste entram —
        # o versionamento tem esse escopo desde a 0112.
        de_volta = [
            p for p in (restored.rglob("*.md") if restored.is_dir() else [restored])
            if p.suffix == ".md" and ws.relpath(p).startswith("testcases/")
        ]
        if de_volta:
            await asyncio.to_thread(
                versioning.commit_paths,
                ws, de_volta, f"restaura {ws.relpath(restored)} da lixeira",
                author_of(request),
            )
        return {"restored": ws.relpath(restored)}

    @app.delete(API_PREFIX + "/trash")
    async def empty_trash(request: Request):
        return {"removed": ws_of(request).empty_trash()}

    # -- tree -------------------------------------------------------------

    @app.get(API_PREFIX + "/tree")
    async def get_tree(request: Request):
        ws, conn = ws_of(request), conn_of(request)
        by_path = {
            row["path"]: dict(row)
            for row in conn.execute(
                "SELECT id, title, type, status, path, created FROM testcases"
            )
        }

        def walk(directory: Path) -> dict:
            node: dict[str, Any] = {
                "name": directory.name,
                "path": ws.relpath(directory),
                "dirs": [],
                "files": [],
            }
            for child in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name)):
                if child.is_dir():
                    node["dirs"].append(walk(child))
                elif child.suffix == ".md":
                    rel = ws.relpath(child)
                    meta = by_path.get(rel)
                    node["files"].append(
                        {
                            "path": rel,
                            "id": meta["id"] if meta else None,
                            "title": meta["title"] if meta else child.stem,
                            "type": meta["type"] if meta else None,
                            "status": meta["status"] if meta else None,
                            "created": meta["created"] if meta else None,
                        }
                    )
            return node

        root = walk(ws.root / "testcases")
        root["name"] = "testcases"
        return root

    # -- requirements ----------------------------------------------------

    @app.get(API_PREFIX + "/requirements")
    async def list_requirements(
        request: Request, kind: str = "", status: str = "", squad: str = ""
    ):
        sql, params = "SELECT * FROM requirements WHERE 1=1", []
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if status:
            sql += " AND status = ?"
            params.append(status)
        if squad:
            sql += " AND squad = ?"
            params.append(squad)
        rows = conn_of(request).execute(sql + " ORDER BY id", params).fetchall()
        return [
            {**dict(r), "tags": [t for t in (r["tags"] or "").split(",") if t]}
            for r in rows
        ]

    @app.post(API_PREFIX + "/requirements", status_code=201)
    async def create_requirement(request: Request, payload: RequirementIn):
        ws, conn = ws_of(request), conn_of(request)
        new_id = ws.next_id(payload.kind)
        meta: dict[str, Any] = {
            "id": new_id,
            "kind": payload.kind,
            "title": payload.title,
            "status": payload.status,
            "external_key": payload.external_key,
            "tags": payload.tags,
            "created": date.today().isoformat(),
            "created_by": author_of(request),
        }
        if payload.squad:
            meta["squad"] = payload.squad
        if payload.kind == "story":
            meta["epic"] = payload.epic
            meta["confluence_url"] = payload.confluence_url
        path = ws.root / "requirements" / f"{new_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body)
        reindex_file(ws, conn, path)
        return _req_out(conn, ws, new_id)

    @app.get(API_PREFIX + "/requirements/{entity_id}")
    async def get_requirement(request: Request, entity_id: str):
        return _req_out(conn_of(request), ws_of(request), entity_id)

    @app.get(API_PREFIX + "/requirements/{entity_id}/criteria")
    async def requirement_criteria(request: Request, entity_id: str):
        """Critérios EARS indexados da story (0091), em ordem — cada um com a
        forma detectada (ubiquitous/event/state/unwanted/optional) ou null
        quando fora de EARS."""
        conn = conn_of(request)
        _find_path(conn, "requirements", entity_id)  # 404 se não existe
        rows = conn.execute(
            "SELECT ears_id, ord, text, form FROM criteria WHERE story_id = ?"
            " ORDER BY ord",
            (entity_id,),
        ).fetchall()
        saida = []
        for row in rows:
            criterio = dict(row)
            # Cobertura POR CRITÉRIO (change 0158). "A story tem 4 CTs" não
            # responde a pergunta do time de negócio, que é "este critério
            # foi verificado?" — quatro casos podem cobrir o mesmo critério e
            # deixar três descobertos.
            casos = conn.execute(
                "SELECT t.id, t.title,"
                " (SELECT r.status FROM results r"
                "   WHERE r.testcase_id = t.id"
                "   ORDER BY r.executed_at DESC LIMIT 1) AS last_status"
                " FROM tc_criteria c JOIN testcases t ON t.id = c.testcase_id"
                " WHERE c.ears_id = ? AND t.story_id = ? ORDER BY t.id",
                (row["ears_id"], entity_id),
            ).fetchall()
            criterio["covered_by"] = [dict(c) for c in casos]
            estados = {c["last_status"] for c in casos}
            if not casos:
                criterio["coverage"] = "uncovered"
            elif estados & {"failed", "blocked"}:
                criterio["coverage"] = "failing"
            elif estados == {None}:
                criterio["coverage"] = "untested"
            else:
                criterio["coverage"] = "passing"
            saida.append(criterio)
        return saida

    @app.get(API_PREFIX + "/requirements/{entity_id}/chain")
    async def requirement_chain(request: Request, entity_id: str):
        """Story 360 (0086): a cadeia completa da story — Epic → Story → CTs
        (status de documento + último resultado + nº de evidências +
        execuções que os rodaram) → Defeitos vinculados. Só leitura, SQL
        sobre tabelas já existentes; responde "essa história foi validada?
        qual evidência comprova?" numa chamada."""
        conn = conn_of(request)
        story = conn.execute(
            "SELECT id, title, status, epic_id, squad FROM requirements WHERE id = ?",
            (entity_id,),
        ).fetchone()
        if not story:
            raise _error(404, "not_found", f"{entity_id} não encontrado")
        epic = None
        if story["epic_id"]:
            epic = conn.execute(
                "SELECT id, title, status FROM requirements WHERE id = ?",
                (story["epic_id"],),
            ).fetchone()

        cts = conn.execute(
            "SELECT id, title, type, status FROM testcases WHERE story_id = ?"
            " ORDER BY id",
            (entity_id,),
        ).fetchall()

        testcases: list[dict[str, Any]] = []
        exec_seen: dict[str, dict] = {}
        passing = failing = untested = evidences_total = 0
        for ct in cts:
            cid = ct["id"]
            runs = conn.execute(
                "SELECT r.execution_id, e.name execution_name, r.status,"
                " r.executed_at FROM results r"
                " JOIN executions e ON e.id = r.execution_id"
                " WHERE r.testcase_id = ?"
                " ORDER BY r.executed_at DESC, r.execution_id DESC",
                (cid,),
            ).fetchall()
            ev_count = conn.execute(
                "SELECT COUNT(*) n FROM evidences WHERE testcase_id = ?", (cid,)
            ).fetchone()["n"]
            evidences_total += ev_count
            last = runs[0] if runs else None
            if last is None:
                untested += 1
            elif last["status"] == "passed":
                passing += 1
            else:
                failing += 1
            for r in runs:
                if r["execution_id"] not in exec_seen:
                    exec_seen[r["execution_id"]] = {
                        "id": r["execution_id"], "name": r["execution_name"],
                    }
            testcases.append({
                **dict(ct),
                "last_result": (
                    {"status": last["status"], "executed_at": last["executed_at"]}
                    if last else None
                ),
                "evidence_count": ev_count,
                "executions": [dict(r) for r in runs],
            })

        # metadados das execuções envolvidas (status/data da execution em si)
        executions = []
        if exec_seen:
            ph = ",".join("?" * len(exec_seen))
            executions = [
                dict(r) for r in conn.execute(
                    f"SELECT id, name, status, created_at FROM executions"
                    f" WHERE id IN ({ph}) ORDER BY id DESC",
                    list(exec_seen.keys()),
                )
            ]

        # defeitos vinculados aos CTs da story ou às execuções envolvidas
        defects = []
        ct_ids = [c["id"] for c in cts]
        if ct_ids or exec_seen:
            conds, params = [], []
            if ct_ids:
                conds.append(f"testcase_id IN ({','.join('?' * len(ct_ids))})")
                params += ct_ids
            if exec_seen:
                conds.append(f"execution_id IN ({','.join('?' * len(exec_seen))})")
                params += list(exec_seen.keys())
            defects = [
                dict(r) for r in conn.execute(
                    "SELECT id, title, status, severity, testcase_id, execution_id"
                    f" FROM defects WHERE {' OR '.join(conds)} ORDER BY id",
                    params,
                )
            ]

        return {
            "story": dict(story),
            "epic": dict(epic) if epic else None,
            "testcases": testcases,
            "executions": executions,
            "defects": defects,
            "summary": {
                "testcases": len(cts), "passing": passing, "failing": failing,
                "untested": untested, "executions": len(executions),
                "defects": len(defects), "evidences": evidences_total,
            },
        }

    @app.put(API_PREFIX + "/requirements/{entity_id}")
    async def update_requirement(request: Request, entity_id: str, payload: RequirementUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "requirements", entity_id)
        meta, body = _load_doc(ws, rel)
        changes = payload.model_dump(exclude_unset=True)
        # Requisito que vive no sistema oficial NÃO se edita aqui (change
        # 0158). Editar a cópia produz divergência silenciosa: os dois lados
        # passam a discordar e ninguém é avisado, porque nada falha. Quem
        # quiser mesmo assumir o requisito aqui remove o vínculo primeiro —
        # e aí a decisão fica explícita e registrada.
        vinculos = integ_ops.read_links(meta)
        if vinculos and not _so_vinculo(changes):
            sistemas = ", ".join(v["system"] for v in vinculos)
            raise _error(
                409, "owned_elsewhere",
                f"{entity_id} vive em {sistemas} — editar a cópia daqui faria"
                " os dois lados discordarem em silêncio. Edite no sistema"
                " oficial, ou remova o vínculo"
                f" (DELETE /integrations/links/requirement/{entity_id}/"
                f"{vinculos[0]['system']}) para assumir o requisito aqui.",
            )
        body = changes.pop("body", body)
        if "squad" in changes and not changes["squad"]:
            meta.pop("squad", None)
            changes.pop("squad")
        meta.update(changes)
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        return _req_out(conn, ws, entity_id)

    def _so_vinculo(changes: dict) -> bool:
        """Campos que descrevem o VÍNCULO continuam editáveis num requisito
        externo: apontar melhor para onde ele mora não é divergir dele."""
        return set(changes) <= {"external_key", "confluence_url"}

    @app.delete(API_PREFIX + "/requirements/{entity_id}", status_code=204)
    async def delete_requirement(request: Request, entity_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "requirements", entity_id)
        path = ws.root / rel
        ws.trash(path)
        reindex_file(ws, conn, path)

    # -- testcases ---------------------------------------------------------

    @app.get(API_PREFIX + "/testcases")
    async def list_testcases(
        request: Request,
        story: str = "",
        status: str = "",
        tag: str = "",
        type: str = "",
        priority: str = "",
        folder: str = "",
        squad: str = "",
        q: str = "",
        needs_rerun: bool | None = None,
    ):
        sql, params = "SELECT DISTINCT t.* FROM testcases t", []
        if tag:
            sql += " JOIN tc_tags g ON g.testcase_id = t.id AND g.tag = ?"
            params.append(tag)
        sql += " WHERE 1=1"
        for field, value in (
            ("story_id", story),
            ("status", status),
            ("type", type),
            ("priority", priority),
            ("squad_effective", squad),
        ):
            if value:
                sql += f" AND t.{field} = ?"
                params.append(value)
        if needs_rerun is not None:
            sql += " AND COALESCE(t.needs_rerun, 0) = ?"
            params.append(1 if needs_rerun else 0)
        if folder:
            sql += " AND t.path LIKE ?"
            params.append(f"testcases/{folder.strip('/')}/%")
        if q:
            sql += " AND (t.title LIKE ? OR t.id LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%"])
        rows = conn_of(request).execute(sql + " ORDER BY t.id", params).fetchall()
        return [dict(r) for r in rows]

    @app.post(API_PREFIX + "/testcases", status_code=201)
    async def create_testcase(request: Request, payload: TestcaseIn):
        ws, conn = ws_of(request), conn_of(request)
        if payload.type != "manual" and payload.automation is None:
            raise _error(422, "automation_required",
                         "casos automated/hybrid exigem o bloco 'automation'")
        if payload.automation is not None and not (
            payload.automation.scenario_tag or payload.automation.scenario_name
        ):
            raise _error(422, "automation_link_required",
                         "automation exige scenario_tag OU scenario_name"
                         " (vínculo por tag ou por nome de cenário)")
        new_id = ws.next_id("testcase")
        today = date.today().isoformat()
        meta: dict[str, Any] = {
            "id": new_id,
            "title": payload.title,
            "type": payload.type,
            "priority": payload.priority,
            "status": payload.status,
            "tags": payload.tags,
            "story": payload.story,
            "created": today,
            "updated": today,
            "created_by": author_of(request),
        }
        if payload.squad:
            meta["squad"] = payload.squad
        if payload.automation is not None:
            meta["automation"] = payload.automation.model_dump(exclude_none=True)
        if payload.criteria:
            meta["criteria"] = payload.criteria
        folder = payload.folder.strip("/").replace("\\", "/")
        target_dir = ws.root / "testcases" / folder if folder else ws.root / "testcases"
        if not str(target_dir.resolve()).startswith(str((ws.root / "testcases").resolve())):
            raise _error(422, "invalid_folder", "folder fora de testcases/")
        path = target_dir / f"{new_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body if payload.body is not None else DEFAULT_TC_BODY)
        reindex_file(ws, conn, path)
        # Um commit por ACAO (change 0112), nao por gravacao — e nunca
        # derrubando a escrita do usuario se o git falhar.
        await asyncio.to_thread(
            versioning.commit_paths,
            ws, [path], f"cria {new_id}: {payload.title}", author_of(request)
        )
        return _tc_out(conn, ws, new_id)

    # -- repositório de pastas (doc de ajustes §1.1) ------------------------
    # ATENÇÃO: rotas estáticas ("/testcases/folders") DEVEM vir antes das
    # dinâmicas ("/testcases/{entity_id}"), senão o FastAPI captura "folders"
    # como entity_id e devolve 404.

    def _safe_area_dir(ws: Workspace, area: str, folder: str) -> Path:
        """Resolve <area>/<folder> com guarda de path traversal."""
        base = ws.root / area
        folder = (folder or "").strip("/").replace("\\", "/")
        target = base / folder if folder else base
        if not str(target.resolve()).startswith(str(base.resolve())):
            raise _error(422, "invalid_folder", f"folder fora de {area}/")
        return target

    @app.post(API_PREFIX + "/testcases/folders", status_code=201)
    async def create_tc_folder(request: Request, payload: FolderIn):
        ws = ws_of(request)
        target = _safe_area_dir(ws, "testcases", payload.path)
        if target == ws.root / "testcases":
            raise _error(422, "invalid_folder", "informe o nome da pasta")
        target.mkdir(parents=True, exist_ok=True)
        return {"path": ws.relpath(target)}

    @app.delete(API_PREFIX + "/testcases/folders", status_code=204)
    async def delete_tc_folder(request: Request, path: str = ""):
        ws, conn = ws_of(request), conn_of(request)
        target = _safe_area_dir(ws, "testcases", path)
        if target == ws.root / "testcases" or not target.is_dir():
            raise _error(422, "invalid_folder", "pasta inválida")
        affected = list(target.rglob("*.md"))
        ws.trash(target)  # move a pasta inteira p/ a lixeira
        for md in affected:
            reindex_file(ws, conn, md)  # não existe mais → remove do índice
        # Uma acao em lote e uma acao (change 0121): sem este commit os
        # casos ficariam apagados na arvore e presentes no historico, e
        # nenhuma acao futura os recolheria.
        if affected:
            await asyncio.to_thread(
                versioning.commit_paths,
                ws, affected, f"exclui a pasta {path or 'testcases/'}"
                f" ({len(affected)} casos)", author_of(request),
            )
        return None

    @app.post(API_PREFIX + "/testcases/folders/move")
    async def move_tc_folder(request: Request, payload: FolderMoveIn):
        # rota estática ("/testcases/folders/move") ANTES de "/testcases/{entity_id}"
        # (mesma armadilha de roteamento das demais rotas de pasta acima).
        ws, conn = ws_of(request), conn_of(request)
        src = _safe_area_dir(ws, "testcases", payload.path)
        if src == ws.root / "testcases" or not src.is_dir():
            raise _error(422, "invalid_folder", "pasta de origem inválida")
        dest_parent = _safe_area_dir(ws, "testcases", payload.dest)
        dest = dest_parent / src.name
        if dest.resolve() == src.resolve():
            return {"path": ws.relpath(src)}  # já está lá — no-op
        if str(dest.resolve()).startswith(str(src.resolve()) + os.sep):
            raise _error(
                422, "invalid_folder", "não é possível mover uma pasta para dentro dela mesma"
            )
        if dest.exists():
            raise _error(409, "conflict", f"{src.name} já existe no destino")
        affected = list(src.rglob("*.md"))  # caminhos antigos, antes do rename
        dest_parent.mkdir(parents=True, exist_ok=True)
        src.rename(dest)
        for old_md in affected:
            reindex_file(ws, conn, old_md)  # caminho antigo não existe mais → remove
        movidos = list(dest.rglob("*.md"))
        for new_md in movidos:
            reindex_file(ws, conn, new_md)  # indexa no caminho novo
        # As duas pontas no MESMO commit, como no move de um caso: e o que
        # faz o `--follow` enxergar a mudanca de pasta como renomeacao.
        if affected or movidos:
            await asyncio.to_thread(
                versioning.commit_paths,
                ws, affected + movidos,
                f"move a pasta {ws.relpath(src)} para {ws.relpath(dest)}",
                author_of(request),
            )
        return {"path": ws.relpath(dest)}

    @app.get(API_PREFIX + "/testcases/impact")
    async def testcases_impact(request: Request, files: str = ""):
        """Quais casos um conjunto de arquivos alterados afeta (change 0146).

        Devolve as duas origens SEPARADAS de propósito: vínculo explícito por
        tag de cenário (ADR 0003) é fato; correlação por mapa de risco é
        palpite útil. Misturar as duas faria quem consome tratar palpite como
        fato — e um agente faria isso em silêncio.

        O caminho vem de um diff (repo-relativo) e o índice guarda o caminho
        relativo ao `local_path` do target: podem ter prefixos diferentes se o
        repo de automação for subpasta. Casa por SUFIXO nos dois sentidos, que
        cobre os dois casos sem exigir configuração."""
        conn = conn_of(request)
        alterados = [f.strip().lstrip("./") for f in files.split(",") if f.strip()]
        if not alterados:
            raise _error(422, "files_required",
                         "informe `files` — a lista de arquivos alterados")

        def casa(indexado: str) -> bool:
            ind = (indexado or "").lstrip("./")
            return any(
                ind and (ind.endswith(a) or a.endswith(ind)) for a in alterados
            )

        por_tag = []
        for row in conn.execute(
            "SELECT id, title, scenario_tag, feature_path, automation_target,"
            " status, COALESCE(needs_rerun, 0) needs_rerun FROM testcases"
            " WHERE feature_path IS NOT NULL"
        ).fetchall():
            if casa(row["feature_path"]):
                por_tag.append({**dict(row), "needs_rerun": bool(row["needs_rerun"])})

        # correlação por mapa de risco: só existe com `risk_repos` configurado
        cfg_repos = ws_of(request).config().get("risk_repos") or []
        por_risco: list[dict] = []
        nota_risco = None
        if not cfg_repos:
            nota_risco = ("mapa de risco não configurado (`risk_repos` vazio no"
                          " arbites.yaml) — só o vínculo por tag foi avaliado")
        return {
            "changed_files": alterados,
            "by_tag": por_tag,
            "by_risk": por_risco,
            "risk_note": nota_risco,
        }

    @app.get(API_PREFIX + "/testcases/{entity_id}")
    async def get_testcase(request: Request, entity_id: str):
        return _tc_out(conn_of(request), ws_of(request), entity_id)

    @app.put(API_PREFIX + "/testcases/{entity_id}")
    async def update_testcase(request: Request, entity_id: str, payload: TestcaseUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "testcases", entity_id)
        meta, body = _load_doc(ws, rel)
        changes = payload.model_dump(exclude_unset=True)
        body = changes.pop("body", body)
        if "automation" in changes and changes["automation"] is None:
            meta.pop("automation", None)
            changes.pop("automation")
        elif isinstance(changes.get("automation"), dict):
            # não gravar chaves None do vínculo (tag OU nome) no YAML
            changes["automation"] = {
                k: v for k, v in changes["automation"].items() if v is not None
            }
        if "squad" in changes and not changes["squad"]:
            meta.pop("squad", None)
            changes.pop("squad")
        if "criteria" in changes and not changes["criteria"]:
            meta.pop("criteria", None)  # lista vazia/None limpa o vínculo
            changes.pop("criteria")
        if "quarantine" in changes and not changes["quarantine"]:
            meta.pop("quarantine", None)  # false não polui o frontmatter
            changes.pop("quarantine")
        meta.update(changes)
        meta["updated"] = date.today().isoformat()
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        await asyncio.to_thread(
            versioning.commit_paths,
            ws, [ws.root / rel],
            f"edita {entity_id}: {meta.get('title') or rel}", author_of(request),
        )
        return _tc_out(conn, ws, entity_id)

    @app.delete(API_PREFIX + "/testcases/{entity_id}", status_code=204)
    async def delete_testcase(request: Request, entity_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "testcases", entity_id)
        path = ws.root / rel
        ws.trash(path)
        reindex_file(ws, conn, path)
        # O arquivo foi para a lixeira, nao para o vazio: o commit registra
        # que saiu, e o historico continua servindo para recupera-lo.
        await asyncio.to_thread(
            versioning.commit_paths,
            ws, [path], f"exclui {entity_id}", author_of(request)
        )

    @app.get(API_PREFIX + "/testcases/{entity_id}/raw", response_class=PlainTextResponse)
    async def get_testcase_raw(request: Request, entity_id: str):
        ws = ws_of(request)
        rel = _find_path(conn_of(request), "testcases", entity_id)
        return (ws.root / rel).read_text(encoding="utf-8")

    @app.get(API_PREFIX + "/testcases/{entity_id}/results")
    async def testcase_results(request: Request, entity_id: str):
        """Histórico de resultados do CT (0074): responde "já passou no
        passado?" — leitura pura da tabela `results` JOIN executions,
        mais recente primeiro."""
        conn = conn_of(request)
        _find_path(conn, "testcases", entity_id)  # 404 se o CT não existe
        rows = conn.execute(
            "SELECT r.execution_id, e.name execution_name, r.status,"
            " r.executed_at, r.duration_seconds"
            " FROM results r JOIN executions e ON e.id = r.execution_id"
            " WHERE r.testcase_id = ?"
            " ORDER BY r.executed_at DESC, r.execution_id DESC",
            (entity_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    @app.put(API_PREFIX + "/testcases/{entity_id}/raw")
    async def put_testcase_raw(request: Request, entity_id: str, payload: RawIn):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "testcases", entity_id)
        (ws.root / rel).write_text(payload.content, encoding="utf-8")
        reindex_file(ws, conn, ws.root / rel)
        await asyncio.to_thread(
            versioning.commit_paths,
            ws, [ws.root / rel], f"edita {entity_id} (markdown cru)",
            author_of(request),
        )
        return _tc_out(conn, ws, entity_id)

    @app.post(API_PREFIX + "/testcases/{entity_id}/move")
    async def move_testcase(request: Request, entity_id: str, payload: MoveIn):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "testcases", entity_id)
        src = ws.root / rel
        dest_dir = _safe_area_dir(ws, "testcases", payload.folder)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        if dest.resolve() != src.resolve():
            if dest.exists():
                raise _error(409, "conflict", f"{dest.name} já existe no destino")
            src.rename(dest)
            reindex_file(ws, conn, src)   # remove o caminho antigo do índice
            reindex_file(ws, conn, dest)  # indexa o novo
            # As duas pontas no MESMO commit: e o que faz o `--follow` do
            # historico enxergar a mudanca de pasta como renomeacao.
            await asyncio.to_thread(
                versioning.commit_paths,
                ws, [src, dest],
                f"move {entity_id} para {payload.folder or 'testcases/'}",
                author_of(request),
            )
        return _tc_out(conn, ws, entity_id)

    # -- versões do caso de teste (change 0112) ----------------------------

    def _tc_rel(request: Request, entity_id: str) -> str:
        return _find_path(conn_of(request), "testcases", entity_id)

    @app.get(API_PREFIX + "/testcases/{entity_id}/versions")
    async def list_versions(request: Request, entity_id: str, limit: int = 50):
        """Antes de responder, recolhe o que foi editado por fora: quem
        mexeu no arquivo no Obsidian tambem merece aparecer no historico."""
        ws = ws_of(request)
        rel = _tc_rel(request, entity_id)
        await asyncio.to_thread(versioning.commit_external_edits, ws, rel)
        return {
            "versions": await asyncio.to_thread(
                versioning.history, ws, rel, limit
            )
        }

    @app.get(API_PREFIX + "/testcases/{entity_id}/versions/diff",
             response_class=PlainTextResponse)
    async def diff_versions(request: Request, entity_id: str, a: str, b: str = ""):
        ws = ws_of(request)
        rel = _tc_rel(request, entity_id)
        try:
            return await asyncio.to_thread(versioning.diff, ws, rel, a, b or None)
        except versioning.GitUnavailable as exc:
            raise _error(422, "git_failed", str(exc)) from None

    @app.get(API_PREFIX + "/testcases/{entity_id}/versions/{sha}",
             response_class=PlainTextResponse)
    async def version_content(request: Request, entity_id: str, sha: str):
        ws = ws_of(request)
        rel = _tc_rel(request, entity_id)
        try:
            return await asyncio.to_thread(versioning.content_at, ws, sha, rel)
        except versioning.GitUnavailable:
            raise _error(404, "version_not_found",
                         f"{sha} nao tem este arquivo") from None

    @app.post(API_PREFIX + "/testcases/{entity_id}/versions/{sha}/restore")
    async def restore_version(request: Request, entity_id: str, sha: str):
        """Restaurar grava um commit NOVO: o historico entre a versao
        restaurada e hoje continua la para quem for entender por que."""
        ws, conn = ws_of(request), conn_of(request)
        rel = _tc_rel(request, entity_id)
        try:
            await asyncio.to_thread(
                versioning.restore, ws, sha, rel, author_of(request)
            )
        except versioning.GitUnavailable:
            raise _error(404, "version_not_found",
                         f"{sha} nao tem este arquivo") from None
        reindex_file(ws, conn, ws.root / rel)
        return _tc_out(conn, ws, entity_id)

    # -- executions (M1) ---------------------------------------------------

    def _save_and_index(ws: Workspace, conn, execution: dict) -> None:
        path = exec_ops.save(ws, execution)
        reindex_file(ws, conn, path)

    @app.get(API_PREFIX + "/executions")
    async def list_executions(
        request: Request, sprint: str = "", status: str = "", origin: str = "", squad: str = ""
    ):
        conn = conn_of(request)
        sql, params = "SELECT * FROM executions WHERE 1=1", []
        for field, value in (
            ("sprint", sprint),
            ("status", status),
            ("origin", origin),
            ("squad", squad),
        ):
            if value:
                sql += f" AND {field} = ?"
                params.append(value)
        rows = conn.execute(sql + " ORDER BY id DESC", params).fetchall()
        out = []
        for row in rows:
            counts = {
                r["status"]: r["c"]
                for r in conn.execute(
                    "SELECT status, COUNT(*) c FROM results WHERE execution_id = ?"
                    " GROUP BY status",
                    (row["id"],),
                )
            }
            out.append({**dict(row), "result_counts": counts})
        return out

    @app.post(API_PREFIX + "/executions", status_code=201)
    async def create_execution(request: Request, payload: ExecutionCreate):
        ws, conn = ws_of(request), conn_of(request)
        if not payload.testcase_ids:
            raise _error(422, "empty_execution", "informe ao menos um testcase_id")
        testcases = []
        for ct_id in payload.testcase_ids:
            row = conn.execute(
                "SELECT id, path FROM testcases WHERE id = ?", (ct_id,)
            ).fetchone()
            if not row:
                raise _error(404, "not_found", f"{ct_id} não encontrado no índice")
            doc = parse_markdown(ws.root / row["path"])
            testcases.append({"id": ct_id, "steps": doc.steps})
        execution = exec_ops.create(
            ws, payload.name, author_of(request), payload.sprint,
            payload.environment, testcases, squad=payload.squad,
            starts_on=payload.starts_on, ends_on=payload.ends_on,
        )
        _save_and_index(ws, conn, execution)
        return execution

    @app.get(API_PREFIX + "/executions/diff")
    async def diff_executions(request: Request, a: str, b: str):
        """Compara os resultados por CT de duas executions (a → b).

        Categorias: regressed / fixed / added (só em b) / removed (só em a) /
        unchanged. Leitura pura da tabela `results` (registrada antes da rota
        `/{exec_id}` para não ser capturada como path param)."""
        conn = conn_of(request)
        for eid in (a, b):
            if not conn.execute(
                "SELECT 1 FROM executions WHERE id = ?", (eid,)
            ).fetchone():
                raise _error(404, "not_found", f"{eid} não encontrada")

        def _results(eid: str) -> dict[str, str]:
            return {
                row["testcase_id"]: row["status"]
                for row in conn.execute(
                    "SELECT testcase_id, status FROM results WHERE execution_id = ?",
                    (eid,),
                )
            }

        ra, rb = _results(a), _results(b)
        ids = sorted(set(ra) | set(rb))
        titles: dict[str, str] = {}
        if ids:
            placeholders = ",".join("?" * len(ids))
            titles = {
                row["id"]: row["title"]
                for row in conn.execute(
                    f"SELECT id, title FROM testcases WHERE id IN ({placeholders})",
                    ids,
                )
            }
        categories: dict[str, list] = {
            k: [] for k in ("regressed", "fixed", "added", "removed", "unchanged")
        }
        for ct in ids:
            entry = {"testcase_id": ct, "title": titles.get(ct)}
            if ct in ra and ct in rb:
                cat = exec_ops.diff_category(ra[ct], rb[ct])
                categories[cat].append({**entry, "status_a": ra[ct], "status_b": rb[ct]})
            elif ct in rb:
                categories["added"].append({**entry, "status_a": None, "status_b": rb[ct]})
            else:
                categories["removed"].append({**entry, "status_a": ra[ct], "status_b": None})
        return {
            "a": a,
            "b": b,
            "categories": categories,
            "counts": {k: len(v) for k, v in categories.items()},
        }

    @app.get(API_PREFIX + "/executions/{exec_id}")
    async def get_execution(request: Request, exec_id: str):
        """O progresso vem derivado dos resultados a cada leitura, e nao
        guardado: contador gravado e contador que diverge do que ele conta."""
        execution = exec_ops.load(ws_of(request), exec_id)
        return {**execution, "progress": exec_ops.progress(execution)}

    @app.delete(API_PREFIX + "/executions/{exec_id}", status_code=204)
    async def delete_execution(request: Request, exec_id: str):
        """Move a PASTA da execution (JSON + evidências) para a lixeira e
        reindexa — nunca apaga do disco (padrão de trash da casa)."""
        ws, conn = ws_of(request), conn_of(request)
        runner: RunManager = request.app.state.runner
        run = runner.runs.get(exec_id)
        if run and run.status in ("queued", "running"):
            raise _error(409, "run_active",
                         f"{exec_id} tem um run de automação ativo — cancele antes")
        execution = exec_ops.load(ws, exec_id)  # 404 se não existe
        folder = exec_ops.exec_dir(ws, exec_id, execution["created_at"])
        json_path = folder / "execution.json"
        ws.trash(folder)
        # reindex do arquivo removido limpa results/result_events/evidences
        reindex_file(ws, conn, json_path)

    @app.patch(API_PREFIX + "/executions/{exec_id}")
    async def patch_execution(request: Request, exec_id: str, payload: ExecutionPatch):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        if execution["status"] == "closed":
            raise _error(409, "execution_closed", f"{exec_id} está fechada")
        fields = payload.model_dump(exclude_unset=True)
        period = {k: fields.pop(k) for k in ("starts_on", "ends_on") if k in fields}
        for key, value in fields.items():
            execution[key] = value
        if period:
            # O periodo passa pela validacao do modulo (ADR 0013): um ciclo
            # que termina antes de comecar e erro de digitacao, nao estado.
            exec_ops.set_period(
                execution,
                period.get("starts_on", execution.get("starts_on")),
                period.get("ends_on", execution.get("ends_on")),
            )
        _save_and_index(ws, conn, execution)
        return execution

    @app.post(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/status")
    async def post_result_status(
        request: Request, exec_id: str, ct_id: str, payload: ResultStatusIn
    ):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.set_result_status(
            execution, ct_id, payload.status, author_of(request),
            payload.comment, payload.column
        )
        _save_and_index(ws, conn, execution)
        clear_needs_rerun(ws, conn, ct_id)  # resultado novo → limpa re-execução (0090)
        return execution

    @app.post(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/steps/{step_index}")
    async def post_step_status(
        request: Request, exec_id: str, ct_id: str, step_index: int, payload: StepStatusIn
    ):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.set_step_status(
            execution, ct_id, step_index, payload.status, author_of(request)
        )
        _save_and_index(ws, conn, execution)
        return execution

    @app.post(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/assignee")
    async def post_result_assignee(
        request: Request, exec_id: str, ct_id: str, payload: AssigneeIn
    ):
        """Responsavel por um caso dentro do ciclo (ADR 0013): e o que divide
        uma regressao entre duas ou mais pessoas sem duplicar a execution."""
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.set_assignee(execution, ct_id, payload.assignee, author_of(request))
        _save_and_index(ws, conn, execution)
        return execution

    @app.post(
        API_PREFIX + "/executions/{exec_id}/results/{ct_id}/evidences", status_code=201
    )
    async def post_evidence(
        request: Request,
        exec_id: str,
        ct_id: str,
        file: UploadFile = File(...),
        note: str | None = Form(default=None),
    ):
        # Sem `who` no form (change 0115): quem anexou a evidencia e quem
        # esta logado, e nao quem o cliente disser que e.
        ws, conn = ws_of(request), conn_of(request)
        # O arquivo e lido ANTES de carregar a execution (change 0123): um
        # upload grande vai para disco e o `read` suspende a requisicao. Com
        # a suspensao no meio do ciclo carregar-alterar-gravar, dois uploads
        # simultaneos partiam do mesmo estado e o ultimo apagava o registro
        # do primeiro — com 201 nos dois e os dois arquivos ja no disco.
        content = await file.read()
        execution = exec_ops.load(ws, exec_id)
        evidence = exec_ops.add_evidence(
            ws,
            execution,
            ct_id,
            file.filename or "evidencia.bin",
            content,
            file.content_type,
            note,
            author_of(request),
        )
        _save_and_index(ws, conn, execution)
        return evidence

    @app.delete(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/evidences/{index}")
    async def delete_evidence(request: Request, exec_id: str, ct_id: str, index: int):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.remove_evidence(ws, execution, ct_id, index, "local")
        _save_and_index(ws, conn, execution)
        return execution

    @app.post(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/defects")
    async def post_link_defect(
        request: Request, exec_id: str, ct_id: str, payload: DefectLinkIn
    ):
        ws, conn = ws_of(request), conn_of(request)
        _find_path(conn, "defects", payload.defect_id)  # 404 se o defeito não existe
        execution = exec_ops.load(ws, exec_id)
        exec_ops.link_defect(execution, ct_id, payload.defect_id, author_of(request))
        _save_and_index(ws, conn, execution)
        return execution

    @app.delete(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/defects/{defect_id}")
    async def delete_link_defect(request: Request, exec_id: str, ct_id: str, defect_id: str):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.unlink_defect(execution, ct_id, defect_id, author_of(request))
        _save_and_index(ws, conn, execution)
        return execution

    @app.post(API_PREFIX + "/executions/{exec_id}/close")
    async def close_execution(request: Request, exec_id: str):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.close(execution, "local")
        _save_and_index(ws, conn, execution)
        return execution

    # -- metrics / matriz (M1.5) --------------------------------------------

    @app.get(API_PREFIX + "/metrics/summary")
    async def metrics_summary(
        request: Request, sprint: str = "", days: int = 0, epic: str = "", squad: str = ""
    ):
        conn = conn_of(request)
        s, d, sq = sprint or None, days or None, squad or None
        summary = {
            "requirement_coverage": metrics_ops.requirement_coverage(conn, epic or None, sq),
            "execution_coverage": metrics_ops.execution_coverage(conn, s, d, sq),
            "pass_rate": metrics_ops.pass_rate(conn, s, d, sq),
            "blocked_rate": metrics_ops.blocked_rate(conn, s, d, sq),
            "rework_rate": metrics_ops.rework_rate(conn, s, d, sq),
        }
        thresholds = ws_of(request).config().get("metric_thresholds")
        annotated = metrics_ops.annotate_thresholds(summary, thresholds)
        # contagem SEMPRE visível de quarentenados (excluídos do pass rate)
        annotated["quarantine"] = metrics_ops.quarantine(conn, sq)
        return annotated

    @app.post(API_PREFIX + "/ai/executive-summary")
    async def ai_executive_summary(request: Request, payload: ExecutiveSummaryIn):
        """0098: resumo executivo narrado pela IA a partir dos NÚMEROS já
        apurados (preview editável, sem gravar). Sem provider → 409, e o
        dashboard segue 100% funcional."""
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        context_md = metrics_ops.executive_context_markdown(
            conn, payload.sprint or None, payload.squad or None
        )
        result = await asyncio.to_thread(
            ai_ops.generate_executive_summary, provider, _with_memory(request, context_md)
        )
        return {"preview": True, **result.model_dump(), "context_markdown": context_md}

    @app.get(API_PREFIX + "/metrics/trend")
    async def metrics_trend(request: Request, days: int = 7, sprint: str = "", squad: str = ""):
        if days not in (7, 15, 30):
            raise _error(422, "invalid_days", "days deve ser 7, 15 ou 30")
        return metrics_ops.trend(conn_of(request), days, sprint or None, squad or None)

    @app.get(API_PREFIX + "/metrics/coverage-gaps")
    async def coverage_gaps(
        request: Request, epic: str = "", story: str = "", squad: str = "",
        include_covered: bool = False,
    ):
        """O que falta cobrir — por story E por critério EARS (change 0146).

        A matriz já dizia "3/7 critérios"; o que faltava era QUAIS 4. Um
        número diz que há buraco; a lista diz onde ele está, e é isso que um
        agente (ou uma pessoa) consegue agir em cima."""
        conn = conn_of(request)
        matriz = metrics_ops.traceability(
            conn, epic or None, None, squad or None
        )
        saida = []
        for grupo in matriz["epics"]:
            for s in grupo["stories"]:
                if story and s["id"] != story:
                    continue
                descobertos = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT ears_id, ord, text, form FROM criteria c"
                        " WHERE c.story_id = ? AND NOT EXISTS ("
                        "  SELECT 1 FROM tc_criteria x"
                        "  JOIN testcases t ON t.id = x.testcase_id"
                        "  WHERE x.ears_id = c.ears_id AND t.story_id = c.story_id)"
                        " ORDER BY ord",
                        (s["id"],),
                    ).fetchall()
                ]
                tem_buraco = s["coverage_state"] == "uncovered" or descobertos
                if not tem_buraco and not include_covered:
                    continue
                saida.append({
                    "story_id": s["id"],
                    "title": s["title"],
                    "epic_id": grupo["id"],
                    "coverage_state": s["coverage_state"],
                    "ct_count": s["ct_count"],
                    "criteria_total": s["criteria_total"],
                    "criteria_covered": s["criteria_covered"],
                    "uncovered_criteria": descobertos,
                })
        return {"stories": saida, "count": len(saida)}

    @app.get(API_PREFIX + "/metrics/coverage")
    async def metrics_coverage(request: Request, epic: str = "", squad: str = ""):
        return metrics_ops.requirement_coverage(conn_of(request), epic or None, squad or None)

    @app.get(API_PREFIX + "/metrics/flaky")
    async def metrics_flaky(request: Request, window: int = 5, squad: str = ""):
        return metrics_ops.flaky(conn_of(request), window, squad or None)

    @app.get(API_PREFIX + "/metrics/defects")
    async def metrics_defects(request: Request, squad: str = ""):
        return metrics_ops.defects_report(conn_of(request), squad or None)

    @app.get(API_PREFIX + "/metrics/activity")
    async def metrics_activity(request: Request, days: int = 371, year: int = 0):
        return metrics_ops.activity_heatmap(conn_of(request), days, year or None)

    @app.get(API_PREFIX + "/metrics/health")
    async def metrics_health(
        request: Request, sprint: str = "", days: int = 0, squad: str = ""
    ):
        ws = ws_of(request)
        cfg = ws.config()
        weights = (cfg.get("health_score") or {}).get("weights")
        pattern = (cfg.get("ci_monitoring") or {}).get("name_pattern")
        return metrics_ops.health_score(
            conn_of(request), weights, sprint or None, days or None, squad or None,
            pattern,
        )

    # -- Dashboard executivo (painel de decisão, capability reporting) ------
    # Consolida sinais que já existem: variação vs período anterior, alertas
    # de risco (achados `bad` do Auditor + Health Score baixo), top problemas
    # (automação/defeitos) e ações recomendadas (achados reformulados como
    # "faça X"). Nada de coleta nova — orquestra os reports existentes.

    _ACTION_VERB = {
        "uncovered_story": "Criar cobertura para",
        "forgotten_defect": "Registrar causa raiz e tratar",
        "aging_defect": "Revisar/fechar",
        "broken_automation": "Investigar automação quebrada:",
    }

    @app.get(API_PREFIX + "/metrics/dashboard")
    async def metrics_dashboard(
        request: Request, sprint: str = "", days: int = 30, squad: str = ""
    ):
        ws, conn = ws_of(request), conn_of(request)
        cfg = ws.config()
        pattern = (cfg.get("ci_monitoring") or {}).get("name_pattern")
        audit_cfg = cfg.get("audit") or {}
        s, sq = sprint or None, squad or None

        findings = audit_ops.collect_findings(
            conn, audit_cfg.get("defect_aging_days"),
            audit_cfg.get("broken_automation_days"), pattern,
        )
        weights = (cfg.get("health_score") or {}).get("weights")
        health = metrics_ops.health_score(conn, weights, s, days or None, sq, pattern)

        # alertas de risco = achados `bad` + Health Score baixo
        alerts = [
            {"severity": f["severity"], "category": f["category"],
             "message": f["message"], "ref": f["ref"]}
            for f in findings if f["severity"] == "bad"
        ]
        if health["score"] is not None and health["score"] < 50:
            alerts.insert(0, {
                "severity": "bad", "category": "health",
                "message": f"Health Score baixo: {health['score']}/100", "ref": None,
            })

        # ações recomendadas = achados (bad+warn) reformulados como "faça X"
        recommended_actions = [
            {"message": f"{_ACTION_VERB.get(f['code'], 'Tratar')} {f['ref'] or f['message']}",
             "ref": f["ref"], "category": f["category"]}
            for f in findings if f["severity"] in ("bad", "warn")
        ][:8]

        reindex_row = conn.execute(
            "SELECT value FROM index_meta WHERE key = 'last_reindex'"
        ).fetchone()
        return {
            "last_reindex": reindex_row["value"] if reindex_row else None,
            "pass_rate_trend": metrics_ops.period_pass_rate(conn, days, s, sq),
            "alerts": alerts,
            "top_problems": metrics_ops.top_problems(conn, pattern, days or None),
            "recommended_actions": recommended_actions,
        }

    @app.get(API_PREFIX + "/metrics/automation")
    async def metrics_automation(request: Request, days: int = 0, env: str = ""):
        ws = ws_of(request)
        pattern = (ws.config().get("ci_monitoring") or {}).get("name_pattern")
        return metrics_ops.automation_report(
            conn_of(request), pattern, days or None, env or None
        )

    @app.get(API_PREFIX + "/metrics/traceability")
    async def metrics_traceability(
        request: Request, epic: str = "", sprint: str = "", squad: str = ""
    ):
        return metrics_ops.traceability(
            conn_of(request), epic or None, sprint or None, squad or None
        )

    @app.get(API_PREFIX + "/squads")
    async def list_squads(request: Request):
        """Squads conhecidos: declarados no arbites.yaml + distintos no índice."""
        ws, conn = ws_of(request), conn_of(request)
        declared = ws.config().get("squads") or []
        seen = {str(s) for s in declared if s}
        for table, col in (
            ("testcases", "squad_effective"),
            ("requirements", "squad"),
            ("executions", "squad"),
        ):
            for r in conn.execute(
                f"SELECT DISTINCT {col} s FROM {table} WHERE {col} IS NOT NULL AND {col} != ''"
            ):
                seen.add(r["s"])
        return {"squads": sorted(seen)}

    @app.get(API_PREFIX + "/metrics/traceability/export")
    async def metrics_traceability_export(
        request: Request, format: str = "md", epic: str = "", sprint: str = "",
        squad: str = "", summary: str = "",
    ):
        matrix = metrics_ops.traceability(
            conn_of(request), epic or None, sprint or None, squad or None
        )
        if format == "md":
            return PlainTextResponse(
                metrics_ops.matrix_markdown(matrix, summary or None),
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="matriz.md"'},
            )
        if format == "pdf":
            from .export_pdf import matrix_pdf

            return Response(
                content=matrix_pdf(matrix, summary or None),
                media_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="matriz.pdf"'},
            )
        raise _error(422, "invalid_format", "format deve ser md ou pdf")

    @app.get(API_PREFIX + "/context-pack")
    async def get_context_pack(
        request: Request,
        epic: str = "",
        story: str = "",
        squad: str = "",
        testcases: bool = True,
        defects: bool = True,
        decisions: bool = True,
        last_result: bool = False,
        format: str = "md",
    ):
        if not (epic or story or squad):
            raise _error(
                422, "scope_required",
                "informe epic, story ou squad — o context pack não exporta o"
                " workspace inteiro sem escopo",
            )
        ws, conn = ws_of(request), conn_of(request)
        pack = context_pack_ops.build(
            conn, ws.root, epic or None, story or None, squad or None,
            include_testcases=testcases, include_defects=defects,
            include_decisions=decisions, include_last_result=last_result,
        )
        if format == "json":
            scope = {k: v for k, v in (("epic", epic), ("story", story),
                                       ("squad", squad)) if v}
            return {"scope": scope, "counts": pack["counts"],
                    "bytes": pack["bytes"], "markdown": pack["markdown"]}
        return PlainTextResponse(
            pack["markdown"],
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="context-pack.md"'},
        )

    @app.get(API_PREFIX + "/agent-pack")
    async def get_agent_pack(
        request: Request,
        epic: str = "",
        story: str = "",
        squad: str = "",
        layout: str = "agents-md",
    ):
        """Pacote de Agente (0094): ZIP com AGENTS.md + specs/ + skills/ do
        escopo, pronto para colar num repositório. Mesmo escopo obrigatório
        do context-pack."""
        if not (epic or story or squad):
            raise _error(
                422, "scope_required",
                "informe epic, story ou squad — o pacote de agente não exporta"
                " o workspace inteiro sem escopo",
            )
        if layout not in ("agents-md", "claude"):
            raise _error(422, "invalid_layout", "layout deve ser agents-md ou claude")
        ws, conn = ws_of(request), conn_of(request)
        pack = agent_pack_ops.build_pack(
            conn, ws.root, epic or None, story or None, squad or None, layout=layout
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in pack["files"].items():
                zf.writestr(path, content)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="agent-pack.zip"'},
        )

    @app.get(API_PREFIX + "/risk-map")
    async def get_risk_map(request: Request, days: int = 90):
        ws, conn = ws_of(request), conn_of(request)
        cfg = ws.config()
        repos = cfg.get("risk_repos") or []
        pattern = (cfg.get("ci_monitoring") or {}).get("name_pattern")
        return risk_map_ops.build(
            conn, repos, days,
            defect_prefix=ws.id_prefixes()["defect"], name_pattern=pattern,
        )

    @app.get(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/evidences/{index}/file")
    async def download_evidence(request: Request, exec_id: str, ct_id: str, index: int):
        ws = ws_of(request)
        execution = exec_ops.load(ws, exec_id)
        result = next(
            (r for r in execution["results"] if r["testcase_id"] == ct_id), None
        )
        if not result or not 0 <= index < len(result["evidences"]):
            raise _error(404, "not_found", "evidência não encontrada")
        evidence = result["evidences"][index]
        file_path = (
            exec_ops.exec_dir(ws, exec_id, execution["created_at"]) / evidence["path"]
        )
        if not file_path.exists():
            raise _error(404, "not_found", f"arquivo ausente no disco: {evidence['path']}")
        return FileResponse(
            file_path, media_type=evidence["mime"], filename=file_path.name
        )

    # -- automação local (M3) -----------------------------------------------

    def _find_target(ws: Workspace, name: str) -> dict:
        for target in ws.config().get("automation_targets") or []:
            if target.get("name") == name:
                return target
        raise _error(404, "not_found", f"target '{name}' não configurado")

    def _targets_out(ws: Workspace, conn, runner: RunManager) -> list[dict]:
        out = []
        for target in ws.config().get("automation_targets") or []:
            name = target.get("name")
            scenarios = conn.execute(
                "SELECT COUNT(*) c FROM scenarios WHERE target = ?", (name,)
            ).fetchone()["c"]
            out.append(
                {
                    "name": name,
                    "kind": target.get("kind", "behave"),
                    "local_path": target.get("local_path"),
                    "features_glob": target.get("features_glob"),
                    "python_path": target.get("python_path"),
                    "working_dir": target.get("working_dir"),
                    "timeout_minutes": target.get("timeout_minutes"),
                    "github": target.get("github") or None,
                    "scenarios": scenarios,
                    "queue_length": runner.queue_length(str(name)),
                }
            )
        return out

    @app.get(API_PREFIX + "/targets")
    async def list_targets(request: Request):
        ws, conn = ws_of(request), conn_of(request)
        runner: RunManager = request.app.state.runner
        return _targets_out(ws, conn, runner)

    @app.put(API_PREFIX + "/targets")
    async def put_targets(request: Request, payload: AutomationTargetsIn):
        """Substitui `automation_targets` no arbites.yaml (mesmo padrão do
        PUT /ai/providers) — sem precisar abrir o YAML na mão."""
        # Um alvo define o executavel e o cwd do subprocess: escrever aqui
        # equivale a executar codigo no servidor (runner.py).
        ws, conn = ws_of(request), conn_of(request)
        runner: RunManager = request.app.state.runner
        import yaml as _yaml

        config = ws.config()
        # Recusar aqui poupa a viagem inteira (change 0170): o valor errado
        # em `python_path` só falhava na hora de executar, e a execution
        # nascia vazia dizendo "sem resultados".
        for alvo in payload.targets:
            try:
                resolver_python(alvo.python_path)
            except PythonPathError as exc:
                raise _error(422, "bad_python_path",
                             f"alvo '{alvo.name}': {exc}")
        alvos = []
        for t in payload.targets:
            bruto = t.model_dump(exclude_none=True)
            gh = bruto.get("github") or {}
            # Bloco pela metade é pior que bloco ausente: o dispatch acusaria
            # "sem repo/workflow" com o bloco na cara de quem olha o YAML.
            if not (gh.get("repo") and gh.get("workflow")):
                bruto.pop("github", None)
            alvos.append(bruto)
        config["automation_targets"] = alvos
        ws.config_path.write_text(
            _yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        for target in config["automation_targets"]:
            scan_target(ws, conn, target)  # já popula cenários/warnings
        return _targets_out(ws, conn, runner)

    @app.get(API_PREFIX + "/automation/browse-features")
    async def browse_feature_files(
        request: Request,
        local_path: str,
        features_glob: str = DEFAULT_FEATURES_GLOB,
    ):
        """Lista os .feature encontrados em `local_path` (scan avulso, sem
        exigir que o target já exista) — para o form de target mostrar a
        lista real em vez do usuário digitar um glob às cegas."""
        path = Path(local_path)
        if not path.is_dir():
            raise _error(422, "invalid_path", f"pasta não encontrada: {local_path}")
        try:
            features = list_feature_files(path, features_glob)
        except Exception as exc:
            raise _error(422, "scan_error", f"falha ao escanear: {exc}") from exc
        return {"local_path": local_path, "features": features}

    # -- sync .feature ↔ CT por nome (mudança 0075) -------------------------
    # Repo de automação read-only (ADR 0003): o vínculo alternativo à tag é
    # automation.feature_path + scenario_name. A sync classifica cada
    # cenário (linked_tag/linked/modified/new + broken) e o modal decide.

    @app.get(API_PREFIX + "/automation/features-sync")
    async def features_sync_status(request: Request, target: str):
        ws, conn = ws_of(request), conn_of(request)
        cfg = _find_target(ws, target)
        tag_re = ct_tag_re(ws.id_prefixes()["testcase"])
        return feature_sync_ops.sync_status(ws, conn, cfg, tag_re)

    @app.post(API_PREFIX + "/automation/features-sync/apply")
    async def features_sync_apply(request: Request, payload: FeatureSyncApplyIn):
        """Aplica as escolhas do modal: criar CTs (steps verbatim), atualizar
        body de CTs `modified` e re-vincular CTs quebrados. Nada é decidido
        automaticamente — só o que veio na seleção."""
        ws, conn = ws_of(request), conn_of(request)
        cfg = _find_target(ws, payload.target)
        local_path = Path(str(cfg.get("local_path", "")))
        glob = str(cfg.get("features_glob") or DEFAULT_FEATURES_GLOB)
        features = {
            f["path"]: f
            for f in feature_sync_ops.scan_feature_files(local_path, glob)
        }

        def find_scenario(feature_path: str, scenario_name: str) -> tuple[dict, dict]:
            feat = features.get(feature_path)
            if not feat:
                raise _error(422, "feature_not_found",
                             f"{feature_path} não encontrado no target")
            sc = next((s for s in feat["scenarios"] if s["name"] == scenario_name), None)
            if not sc:
                raise _error(422, "scenario_not_found",
                             f'cenário "{scenario_name}" não existe em {feature_path}')
            return feat, sc

        created: list[str] = []
        raiz = (payload.folder or f"automacao/{slugify(payload.target)}").strip("/")
        for item in payload.create:
            feat, sc = find_scenario(item.feature_path, item.scenario_name)
            # Uma pasta por arquivo `.feature`, espelhando a árvore do
            # repositório (change 0171). Antes tudo caía em `raiz` e um
            # projeto com dezenas de features virava uma lista chapada.
            sub = feature_sync_ops.pasta_do_cenario(item.feature_path, glob)
            folder = f"{raiz}/{sub}".strip("/") if sub else raiz
            target_dir = _safe_area_dir(ws, "testcases", folder)
            new_id = ws.next_id("testcase")
            today = date.today().isoformat()
            meta = {
                "id": new_id,
                "title": sc["name"],
                "type": "automated",
                "priority": "medium",
                "status": "ready",
                "automation": {
                    "target": payload.target,
                    "feature_path": item.feature_path,
                    "scenario_name": item.scenario_name,
                },
                "created": today,
                "updated": today,
            }
            body = feature_sync_ops.scenario_body(
                feat["feature_name"], sc, feat["language"]
            )
            path = target_dir / f"{new_id}-{slugify(sc['name'])}.md"
            _write_doc(path, meta, body)
            reindex_file(ws, conn, path)
            created.append(new_id)

        updated: list[str] = []
        for ct_id in payload.update:
            rel = _find_path(conn, "testcases", ct_id)
            meta, _old_body = _load_doc(ws, rel)
            automation = meta.get("automation") or {}
            feat, sc = find_scenario(
                str(automation.get("feature_path", "")),
                str(automation.get("scenario_name", "")),
            )
            meta["updated"] = date.today().isoformat()
            # re-base consciente de steps → o CT precisa ser re-executado (0090);
            # o flag é limpo quando um resultado novo do CT é registrado
            meta["needs_rerun"] = True
            _write_doc(ws.root / rel, meta, feature_sync_ops.scenario_body(
                feat["feature_name"], sc, feat["language"]
            ))
            reindex_file(ws, conn, ws.root / rel)
            updated.append(ct_id)

        relinked: list[str] = []
        for item in payload.relink:
            rel = _find_path(conn, "testcases", item.ct_id)
            meta, old_body = _load_doc(ws, rel)
            feat, sc = find_scenario(item.feature_path, item.scenario_name)
            automation = dict(meta.get("automation") or {})
            automation["feature_path"] = item.feature_path
            automation["scenario_name"] = item.scenario_name
            meta["automation"] = automation
            meta["updated"] = date.today().isoformat()
            # re-vincular também re-baseia o body nos steps atuais (o CT
            # volta a espelhar o cenário; o diff da sync volta a funcionar)
            _write_doc(ws.root / rel, meta, feature_sync_ops.scenario_body(
                feat["feature_name"], sc, feat["language"]
            ))
            reindex_file(ws, conn, ws.root / rel)
            relinked.append(item.ct_id)

        # re-scan do target: tabela scenarios reflete os vínculos novos
        scan_target(ws, conn, cfg)
        return {"created": created, "updated": updated, "relinked": relinked}

    @app.post(API_PREFIX + "/targets/{name}/scan")
    async def scan_target_route(request: Request, name: str):
        ws, conn = ws_of(request), conn_of(request)
        return scan_target(ws, conn, _find_target(ws, name))

    @app.get(API_PREFIX + "/targets/{name}/features")
    async def target_features(request: Request, name: str):
        """Arquivos .feature e tags do target (para os dropdowns do run).

        Lista do DISCO (mesma fonte do preview `/automation/browse-features`,
        via `list_feature_files`) em vez de só da tabela `scenarios` — um
        repositório sem nenhum cenário tagueado `@CT-` ainda mostra seus
        arquivos aqui (mudança 0067: antes o dropdown ficava vazio e o run
        recusava com 422). `mapped` anota quantos cenários de cada arquivo
        já têm tag reconhecida, para a UI explicar quando é zero.
        """
        ws, conn = ws_of(request), conn_of(request)
        target = _find_target(ws, name)
        local_path = Path(str(target.get("local_path") or ""))
        glob = str(target.get("features_glob") or DEFAULT_FEATURES_GLOB)

        disk_features: list[dict[str, Any]] = []
        if local_path.is_dir():
            try:
                disk_features = list_feature_files(local_path, glob)
            except OSError:
                disk_features = []

        rows = conn.execute(
            "SELECT feature_path, tag, scenario_name FROM scenarios WHERE target = ?"
            " ORDER BY feature_path, line",
            (name,),
        ).fetchall()
        mapped_by_feature: dict[str, int] = {}
        tags: set[str] = set()
        for r in rows:
            mapped_by_feature[r["feature_path"]] = (
                mapped_by_feature.get(r["feature_path"], 0) + 1
            )
            # tags sintéticas de vínculo por nome ("name:<arquivo>:<linha>",
            # mudança 0075) não são tags do behave — fora do dropdown
            if r["tag"].startswith("@"):
                tags.add(r["tag"])

        return {
            "features": [
                {
                    "path": f["path"],
                    "scenarios": f["scenarios"],
                    "mapped": mapped_by_feature.get(f["path"], 0),
                }
                for f in disk_features
            ],
            "tags": sorted(tags),
        }

    _ARTIFACT_KINDS = ("logs", "screenshots", "analise")

    def _artifact_base(ws: Workspace, name: str, kind: str) -> Path:
        target = _find_target(ws, name)
        local = Path(str(target.get("local_path") or ""))
        if kind not in _ARTIFACT_KINDS:
            raise _error(422, "invalid_kind", f"kind deve ser um de {_ARTIFACT_KINDS}")
        return local / kind

    @app.get(API_PREFIX + "/targets/{name}/artifacts")
    async def target_artifacts(request: Request, name: str):
        """Artefatos pós-execução: ./logs, ./screenshots, ./analise (doc §1.5.1)."""
        ws = ws_of(request)
        out: dict[str, list[dict]] = {}
        for kind in _ARTIFACT_KINDS:
            base = _artifact_base(ws, name, kind)
            files = []
            if base.is_dir():
                for f in sorted(base.rglob("*")):
                    if f.is_file():
                        stat = f.stat()
                        files.append({
                            "path": f.relative_to(base).as_posix(),
                            "size": stat.st_size,
                            "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                        })
            out[kind] = files
        return out

    @app.get(API_PREFIX + "/targets/{name}/artifacts/file")
    async def target_artifact_file(request: Request, name: str, kind: str, path: str):
        ws = ws_of(request)
        base = _artifact_base(ws, name, kind)
        file = (base / path).resolve()
        if not str(file).startswith(str(base.resolve())) or not file.is_file():
            raise _error(404, "not_found", "artefato não encontrado")
        return FileResponse(str(file), filename=file.name)

    # -- .env do target (doc §1.5.1 etapa 5) --------------------------------

    def _env_path(ws: Workspace, name: str) -> Path:
        target = _find_target(ws, name)
        local = Path(str(target.get("local_path") or ""))
        if not local.is_dir():
            raise _error(422, "no_local_path", f"target '{name}' sem local_path válido")
        return local / ".env"

    @app.get(API_PREFIX + "/env/catalog")
    async def env_catalog(request: Request, target: str = ""):
        """Catálogo de `.env` derivado do projeto-alvo (0099) — nunca campos
        fixos. Sem target útil ou sem `.env`/`.env.example`, catálogo vazio."""
        if not target:
            return {"catalog": []}
        ws = ws_of(request)
        try:
            cfg = _find_target(ws, target)
        except HTTPException:
            return {"catalog": []}
        local = Path(str(cfg.get("local_path") or ""))
        if not local.is_dir():
            return {"catalog": []}
        return {"catalog": derive_env_catalog(local)}

    @app.get(API_PREFIX + "/targets/{name}/env")
    async def get_target_env(request: Request, name: str):
        path = _env_path(ws_of(request), name)
        values: dict[str, str] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, _, value = stripped.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
        return {"path": str(path), "exists": path.exists(), "values": values}

    @app.put(API_PREFIX + "/targets/{name}/env")
    async def put_target_env(request: Request, name: str, payload: EnvIn):
        """Atualiza chaves no .env preservando comentários e linhas desconhecidas."""
        path = _env_path(ws_of(request), name)
        lines = (
            path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
        )
        pending = dict(payload.values)
        out_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.partition("=")[0].strip()
                if key in pending:
                    out_lines.append(f"{key}={pending.pop(key)}")
                    continue
            out_lines.append(line)
        for key, value in pending.items():  # chaves novas ao final
            out_lines.append(f"{key}={value}")
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return {"path": str(path), "updated": len(payload.values)}

    @app.post(API_PREFIX + "/runs/local", status_code=201)
    async def create_local_run(request: Request, payload: LocalRunIn):
        ws, conn = ws_of(request), conn_of(request)
        runner: RunManager = request.app.state.runner
        target = _find_target(ws, payload.target)

        # resolve seleção → CTs da execution + tags do behave.
        # `features` (0076) e `feature` (legado) somam numa lista única —
        # 1..N arquivos, inclusive de features diferentes, numa execution só.
        feature_files = [f for f in payload.features if f]
        if payload.feature and payload.feature not in feature_files:
            feature_files.append(payload.feature)
        ct_ids: list[str] = list(payload.testcase_ids)
        tags: list[str] = [t if t.startswith("@") else f"@{t}" for t in payload.tags]
        if feature_files and not ct_ids and not tags:
            # rodar arquivos inteiros: CTs = cenários de TODOS os arquivos
            # (vinculados por tag OU por nome — coluna ct_id, mudança 0075)
            placeholders = ",".join("?" for _ in feature_files)
            rows = conn.execute(
                "SELECT tag, ct_id FROM scenarios"
                f" WHERE target = ? AND feature_path IN ({placeholders})",
                (payload.target, *feature_files),
            ).fetchall()
            ct_ids = sorted({
                r["ct_id"] or r["tag"].lstrip("@") for r in rows if r["ct_id"] or r["tag"].startswith("@")
            })
        if tags and not ct_ids:
            rows = conn.execute(
                "SELECT DISTINCT t.id FROM testcases t JOIN tc_tags g"
                " ON g.testcase_id = t.id WHERE g.tag IN (%s)"
                % ",".join("?" for _ in payload.tags),
                payload.tags,
            ).fetchall()
            by_scenario = conn.execute(
                "SELECT tag FROM scenarios WHERE target = ? AND tag IN (%s)"
                % ",".join("?" for _ in tags),
                [payload.target, *tags],
            ).fetchall()
            ct_ids = [r["id"] for r in rows] + [
                r["tag"].lstrip("@") for r in by_scenario
            ]
            ct_ids = sorted(set(ct_ids))
        if not ct_ids and not feature_files:
            raise _error(422, "empty_selection",
                         "informe testcase_ids, tags ou feature que resolvam para CTs")
        # feature sem nenhum cenário mapeado a CT ainda roda: o arquivo
        # inteiro vai pro behave (ct_ids fica vazio, a execution nasce sem
        # CTs vinculados) — vínculo é o caminho para rastreabilidade, não um
        # pré-requisito para executar (mudança 0067)
        if not tags and not feature_files:
            rows = conn.execute(
                "SELECT id, scenario_tag FROM testcases WHERE id IN (%s)"
                % ",".join("?" for _ in ct_ids),
                ct_ids,
            ).fetchall()
            tags = [r["scenario_tag"] or f"@{r['id']}" for r in rows]

        testcases = []
        for ct_id in ct_ids:
            row = conn.execute(
                "SELECT id, path FROM testcases WHERE id = ?", (ct_id,)
            ).fetchone()
            if not row:
                # cenário sem CT espelho no workspace — roda mesmo assim,
                # sem entrada na execution
                continue
            doc = parse_markdown(ws.root / row["path"])
            testcases.append({"id": ct_id, "steps": doc.steps})

        # mapa nome-do-cenário → ct_id (tag e nome-linked) para o progresso
        # ao vivo e para o parse do JSON final casar por nome (0075/0076)
        live_map = {
            r["scenario_name"]: (r["ct_id"] or r["tag"].lstrip("@"))
            for r in conn.execute(
                "SELECT scenario_name, tag, ct_id FROM scenarios WHERE target = ?",
                (payload.target,),
            )
            if r["scenario_name"] and (r["ct_id"] or r["tag"].startswith("@"))
        }
        execution = runner.submit(
            target, testcases, tags, feature=payload.feature,
            features=feature_files, live_map=live_map,
        )
        return {
            "execution": execution,
            "run": runner.runs[execution["id"]].snapshot(),
        }

    @app.get(API_PREFIX + "/runs/active")
    async def runs_active(request: Request):
        """Runs em fila/execução — alimenta o indicador pulsante no menu
        lateral (mudança 0076). Leve: consultado no refresh de 5s do App."""
        runner: RunManager = request.app.state.runner
        active = [
            {"exec_id": r.exec_id, "target": str(r.target.get("name")),
             "status": r.status}
            for r in runner.runs.values() if r.status in ("queued", "running")
        ]
        return {"count": len(active), "runs": active}

    @app.get(API_PREFIX + "/runs/{exec_id}")
    async def run_status(request: Request, exec_id: str):
        runner: RunManager = request.app.state.runner
        run = runner.runs.get(exec_id)
        if not run:
            raise _error(404, "not_found", f"run {exec_id} não existe")
        return run.snapshot()

    @app.get(API_PREFIX + "/runs/{exec_id}/stream")
    async def stream_run(request: Request, exec_id: str):
        runner: RunManager = request.app.state.runner
        run = runner.runs.get(exec_id)
        if not run:
            raise _error(404, "not_found", f"run {exec_id} não existe")

        async def event_stream():
            queue: asyncio.Queue = asyncio.Queue()
            finished = run.status in ("done", "failed", "timeout", "cancelled")
            if not finished:
                run.subscribers.append(queue)
            try:
                for line in list(run.log):  # replay do buffer p/ quem chega tarde
                    yield f"data: {line}\n\n"
                if not finished:
                    while True:
                        try:
                            line = await asyncio.wait_for(
                                queue.get(), timeout=SSE_KEEPALIVE_SECONDS
                            )
                        except asyncio.TimeoutError:
                            # Passo silencioso do Behave: sem isto a conexao
                            # fica sem trafego, e um proxy no caminho (o
                            # Cloudflare Tunnel corta conexao ociosa por
                            # volta de 100s) derruba um run que esta vivo.
                            # `:` e comentario SSE — o EventSource ignora,
                            # entao o terminal da UI nao ve nada.
                            yield ": keepalive\n\n"
                            continue
                        if line is None:
                            break
                        yield f"data: {line}\n\n"
                yield f"event: done\ndata: {run.status}\n\n"
            finally:
                if queue in run.subscribers:
                    run.subscribers.remove(queue)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.post(API_PREFIX + "/runs/{exec_id}/cancel")
    async def cancel_run(request: Request, exec_id: str):
        runner: RunManager = request.app.state.runner
        return runner.cancel(exec_id).snapshot()

    # -- GitHub Actions (M4) --------------------------------------------------

    @app.post(API_PREFIX + "/runs/ci", status_code=201)
    async def create_ci_run(request: Request, payload: CIRunIn):
        ws, conn = ws_of(request), conn_of(request)
        ci: CIManager = request.app.state.ci
        ct_ids = list(payload.testcase_ids)
        if payload.tags and not ct_ids:
            rows = conn.execute(
                "SELECT id FROM testcases WHERE scenario_tag IN (%s)"
                % ",".join("?" for _ in payload.tags),
                [t if t.startswith("@") else f"@{t}" for t in payload.tags],
            ).fetchall()
            ct_ids = [r["id"] for r in rows]
        testcases = []
        for ct_id in ct_ids:
            row = conn.execute(
                "SELECT id, path FROM testcases WHERE id = ?", (ct_id,)
            ).fetchone()
            if not row:
                raise _error(404, "not_found", f"{ct_id} não encontrado")
            doc = parse_markdown(ws.root / row["path"])
            testcases.append({"id": ct_id, "steps": doc.steps})
        if not testcases:
            raise _error(422, "empty_selection",
                         "informe testcase_ids ou tags que resolvam para CTs")
        inputs = {"tags": ",".join(
            t if t.startswith("@") else f"@{t}" for t in payload.tags
        )} if payload.tags else {"tags": ",".join(f"@{c}" for c in ct_ids)}
        # parâmetros do workflow corporativo (doc §1.5.2) — só os informados
        for key, value in (
            ("feature", payload.feature),
            ("environment", payload.environment),
            ("browser", payload.browser),
            ("source_repo", payload.source_repo),
        ):
            if value:
                inputs[key] = value
        return await asyncio.to_thread(
            ci.dispatch, payload.target, payload.ref, inputs, testcases
        )

    @app.get(API_PREFIX + "/runs/ci/{exec_id}/status")
    async def ci_run_status(request: Request, exec_id: str):
        ci: CIManager = request.app.state.ci
        return await asyncio.to_thread(ci.status, exec_id)

    @app.post(API_PREFIX + "/runs/ci/{exec_id}/collect")
    async def ci_run_collect(request: Request, exec_id: str):
        ci: CIManager = request.app.state.ci
        return await asyncio.to_thread(ci.collect, exec_id)

    # -- observabilidade: runs ingeridos (changes 0153/0154, ADR 0016) ------
    #
    # Puxar, não receber: a instância é local e não é alcançável da internet.
    # O que já foi ingerido é respondido pelo DISCO, então repetir a ingestão
    # não duplica e uma semana desligado volta inteira.

    @app.get(API_PREFIX + "/ci/sources")
    async def get_ci_sources(request: Request):
        config = ws_of(request).config().get("observability") or {}
        return {"sources": config.get("sources") or [],
                "max_runs_per_poll": config.get("max_runs_per_poll") or 50}

    @app.put(API_PREFIX + "/ci/sources")
    async def put_ci_sources(request: Request, payload: ObservabilitySourcesIn):
        """Declara as origens sem abrir o YAML na mão (change 0173).

        Antes só existiam no arquivo: quem clicava em "Buscar execuções" numa
        instalação nova recebia "nenhuma fonte" e não tinha onde declarar uma.
        """
        ws = ws_of(request)
        import yaml as _yaml

        config = ws.config()
        observabilidade = dict(config.get("observability") or {})
        fontes = []
        for fonte in payload.sources:
            if not fonte.repo.strip():
                continue
            limpa: dict[str, Any] = {"provider": fonte.provider or "github",
                                     "repo": fonte.repo.strip()}
            # Vazio quer dizer "todos": gravar a chave com "" faria a
            # ingestão procurar um workflow chamado string vazia.
            if (fonte.workflow or "").strip():
                limpa["workflow"] = fonte.workflow.strip()
            if (fonte.artifact or "").strip():
                limpa["artifact"] = fonte.artifact.strip()
            fontes.append(limpa)
        observabilidade["sources"] = fontes
        if payload.max_runs_per_poll:
            observabilidade["max_runs_per_poll"] = int(payload.max_runs_per_poll)
        config["observability"] = observabilidade
        ws.config_path.write_text(
            _yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return {"sources": fontes,
                "max_runs_per_poll": observabilidade.get("max_runs_per_poll") or 50}

    @app.post(API_PREFIX + "/ci/ingest")
    async def ci_ingest_now(request: Request, limit: int | None = None):
        ingestor: CIIngestor = request.app.state.ci_ingest
        return await asyncio.to_thread(ingestor.ingerir, limit)

    @app.post(API_PREFIX + "/ci/reprocess")
    async def ci_reprocess(request: Request):
        # Relê os anexos que JÁ estão no disco. Quando o reconhecimento
        # melhora, apagar tudo e rebuscar custaria horas de download para
        # reler arquivos que estão aqui do lado (change 0189).
        ws, conn = ws_of(request), conn_of(request)
        return await asyncio.to_thread(ci_ingest.reprocessar, ws, conn)

    @app.get(API_PREFIX + "/ci/runs")
    async def ci_runs(request: Request, limit: int = 50,
                      workflow: str | None = None):
        return {"runs": ci_ingest.listar_runs(conn_of(request), limit, workflow)}

    @app.get(API_PREFIX + "/ci/observability")
    async def ci_observability(request: Request, days: int = 30):
        """A tela inteira numa chamada: saúde, sinais, o que mudou e os runs.

        Sempre com o período ANTERIOR ao lado — um número sozinho não diz se
        está melhorando, e é essa comparação que separa observabilidade de
        um mural de gráficos.
        """
        if days < 1 or days > 365:
            raise _error(422, "invalid_period", "days deve estar entre 1 e 365")
        return ci_ingest.painel(ws_of(request), conn_of(request), days)

    @app.get(API_PREFIX + "/ci/observability/export")
    async def export_observability(request: Request, format: str = "pdf",
                                   days: int = 30):
        """O painel inteiro em arquivo (change 0174).

        Três formatos porque são três perguntas: a série crua para a planilha
        (csv), o painel em texto para ata e wiki (md), e o painel COM os
        gráficos para anexar e mandar (pdf).
        """
        from . import export_obs

        painel = ci_ingest.painel(ws_of(request), conn_of(request), days)
        sufixo = (painel.get("period") or {}).get("until", "")[:10] or "hoje"
        if format == "findings":
            # Os achados agregados, para a planilha priorizar fora do Arbites
            # (change 0176) — outra pergunta que o csv de série não responde.
            return PlainTextResponse(
                export_obs.achados_csv(painel),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition":
                         f'attachment; filename="acessibilidade-{sufixo}.csv"'},
            )
        if format == "csv":
            return PlainTextResponse(
                export_obs.sinais_csv(painel),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition":
                         f'attachment; filename="observabilidade-{sufixo}.csv"'},
            )
        if format == "md":
            return PlainTextResponse(
                export_obs.painel_markdown(painel),
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition":
                         f'attachment; filename="observabilidade-{sufixo}.md"'},
            )
        if format == "pdf":
            return Response(
                content=export_obs.painel_pdf(painel),
                media_type="application/pdf",
                headers={"Content-Disposition":
                         f'attachment; filename="observabilidade-{sufixo}.pdf"'},
            )
        raise _error(422, "invalid_format",
                     "format deve ser pdf, md, csv ou findings")

    # -- agente de análise da observabilidade (change 0179) ---------------
    #
    # O painel responde perguntas isoladas; ninguém junta as três no fim do
    # dia. O agente junta, escreve o veredito e GUARDA — como artefato do
    # workspace, para o histórico sobreviver a um reindex (ADR 0001).

    @app.post(API_PREFIX + "/ci/analysis")
    async def criar_analise_ci(request: Request, payload: AnaliseCIIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        nome = payload.provider or (_ai_config(ws).get("default_provider") or "")
        quadro = ci_ingest.painel(ws, conn, payload.days)
        if not (quadro.get("health") or {}).get("runs"):
            raise _error(422, "no_runs",
                         "não há execução ingerida no período; não há o que"
                         " analisar")
        analise = await asyncio.to_thread(
            ci_analise.analisar, provider, ws, quadro, nome,
            _with_memory(request, ""),
        )
        _log_agent_event(
            ws, conn, "analyze_observability", analise["id"], analise["id"],
            f"Analisou {payload.days} dia(s) de observabilidade:"
            f" {analise.get('saude_geral')}",
        )
        return analise

    @app.get(API_PREFIX + "/ci/analysis")
    async def listar_analises_ci(request: Request, limit: int = 50):
        return {"analyses": ci_analise.listar(ws_of(request), limit)}

    @app.get(API_PREFIX + "/ci/analysis/{analise_id}")
    async def ler_analise_ci(request: Request, analise_id: str):
        try:
            return ci_analise.ler(ws_of(request), analise_id)
        except ci_analise.AnaliseError as e:
            raise _error(e.status, e.code, e.message)

    @app.post(API_PREFIX + "/ci/analysis/compare")
    async def comparar_analises_ci(request: Request, payload: CompararAnalisesIn):
        """Compara duas análises guardadas — sempre da mais velha para a mais
        nova, porque "melhorou" depende de qual veio antes."""
        ws = ws_of(request)
        provider = _ai_provider(request, payload.provider)
        try:
            return await asyncio.to_thread(
                ci_analise.comparar, provider, ws, payload.a, payload.b)
        except ci_analise.AnaliseError as e:
            raise _error(e.status, e.code, e.message)

    @app.get(API_PREFIX + "/ci/retention")
    async def ci_retention_preview(request: Request):
        """O que está ocupado e o que a próxima limpeza levaria — ANTES de
        levar. Limpeza que só diz o que fez depois de feita obriga a confiar
        sem poder conferir (change 0156)."""
        return await asyncio.to_thread(ci_retencao.previa, ws_of(request))

    @app.post(API_PREFIX + "/ci/retention/apply")
    async def ci_retention_apply(request: Request):
        return await asyncio.to_thread(
            ci_retencao.aplicar, ws_of(request), conn_of(request)
        )

    @app.get(API_PREFIX + "/ci/runs/{run_id}")
    async def ci_run_detail(request: Request, run_id: str):
        return ci_ingest.run_detalhado(ws_of(request), conn_of(request), run_id)

    @app.get(API_PREFIX + "/ci/evidences")
    async def ci_evidencias(request: Request, days: int = 30,
                            kind: str = "", origin: str = "",
                            failures_only: bool = False, limit: int = 120):
        """Prints e logs do PERÍODO (change 0180).

        Até aqui a evidência só existia dentro da descida: para ver o print da
        falha era preciso já saber em qual execução ela aconteceu.
        """
        _, inicio, fim = ci_ingest._dias_atras(days)
        return ci_ingest.evidencias(
            conn_of(request), inicio, fim, kind or None, origin or None,
            failures_only, limit,
        )

    @app.get(API_PREFIX + "/ci/attachment")
    async def ci_attachment(request: Request, path: str):
        """Serve o print/log/anexo do run. O caminho vem do índice, mas a
        contenção é verificada no disco assim mesmo: um índice adulterado não
        pode virar leitura de arquivo arbitrário."""
        ws = ws_of(request)
        base = (ws.root / "ci").resolve()
        alvo = (ws.root / path).resolve()
        if not str(alvo).startswith(str(base) + os.sep) or not alvo.is_file():
            raise _error(404, "not_found", f"anexo ausente: {path}")
        return FileResponse(alvo)

    @app.get(API_PREFIX + "/ci/signals")
    async def ci_signal_names(request: Request):
        """Os sinais que EXISTEM — descobertos do que chegou, não de uma lista
        fixa no código: um sinal novo aparece aqui sem deploy."""
        return {"signals": ci_ingest.nomes_de_sinal(conn_of(request))}

    @app.get(API_PREFIX + "/ci/signals/{name}")
    async def ci_signal_series(request: Request, name: str,
                               since: str | None = None,
                               until: str | None = None):
        return ci_ingest.serie(conn_of(request), name, since, until)

    # -- identidade externa (change 0145, ADR 0015) -------------------------
    #
    # O vínculo mora no FRONTMATTER, não só no índice: o índice é descartável
    # (ADR 0001) e um reindex apagaria a memória do que já foi sincronizado —
    # e aí a próxima sincronia recriaria no sistema oficial tudo o que já
    # existe lá.

    _VINCULAVEIS = {"testcase": "testcases", "requirement": "requirements"}

    def _tabela_de(kind: str) -> str:
        if kind not in _VINCULAVEIS:
            raise _error(
                422, "unlinkable_kind",
                "só caso de teste e requisito têm vínculo externo; recebido: %s" % kind,
            )
        return _VINCULAVEIS[kind]

    @app.get(API_PREFIX + "/integrations/links")
    async def external_links(request: Request, system: str = "", state: str = ""):
        """O que daqui está ligado a quê lá, e em que estado.

        É a consulta que torna qualquer escrita idempotente: antes de criar
        no sistema oficial, pergunte o que já existe. `state` filtra por
        pendência — `local_changed` é o que falta empurrar."""
        ws, conn = ws_of(request), conn_of(request)
        saida = []
        for kind, tabela in _VINCULAVEIS.items():
            for row in conn.execute(
                f"SELECT id, title, path FROM {tabela} ORDER BY id"
            ).fetchall():
                try:
                    meta, corpo = _load_doc(ws, row["path"])
                except (OSError, ValueError):
                    continue
                agora = integ_ops.content_hash(corpo)
                vinculos = integ_ops.read_links(meta)
                if system:
                    vinculos = [v for v in vinculos if v["system"] == system]
                for v in vinculos:
                    estado = integ_ops.sync_state(v, agora)
                    if state and estado != state:
                        continue
                    saida.append({
                        "kind": kind, "entity_id": row["id"], "title": row["title"],
                        "system": v["system"], "remote_id": v["id"],
                        "revision": v.get("revision"),
                        "synced_at": v.get("synced_at"), "state": estado,
                    })
                # Artefato sem vínculo TAMBÉM é resposta: ele é o
                # `never_synced`, e é justamente o que alguém pede quando
                # pergunta "o que ainda não foi para lá?". Filtrar por
                # sistema o exclui — ele não pertence a sistema nenhum.
                if not vinculos and not system and state in ("", "never_synced"):
                    saida.append({
                        "kind": kind, "entity_id": row["id"], "title": row["title"],
                        "system": None, "remote_id": None, "revision": None,
                        "synced_at": None, "state": "never_synced",
                    })
        return {"links": saida, "count": len(saida)}

    @app.put(API_PREFIX + "/integrations/links/{kind}/{entity_id}")
    async def set_external_link(
        request: Request, kind: str, entity_id: str, payload: ExternalLinkIn
    ):
        """Registra (ou atualiza) o vínculo de UM sistema, preservando os
        outros: numa migração corporativa os dois convivem, e perder o antigo
        enquanto o novo nasce é perder o rastro quando ele mais importa."""
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, _tabela_de(kind), entity_id)
        meta, corpo = _load_doc(ws, rel)
        meta[integ_ops.CAMPO] = integ_ops.upsert_link(
            meta, payload.system, payload.id, payload.revision,
            payload.synced_hash or integ_ops.content_hash(corpo),
            datetime.now(timezone.utc).isoformat(),
        )
        path = ws.root / rel
        _write_doc(path, meta, corpo)
        reindex_file(ws, conn, path)
        return {"entity_id": entity_id, "external": meta[integ_ops.CAMPO]}

    @app.delete(API_PREFIX + "/integrations/links/{kind}/{entity_id}/{system}",
                status_code=204)
    async def delete_external_link(
        request: Request, kind: str, entity_id: str, system: str
    ):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, _tabela_de(kind), entity_id)
        meta, corpo = _load_doc(ws, rel)
        restantes = integ_ops.remove_link(meta, system)
        if restantes:
            meta[integ_ops.CAMPO] = restantes
        else:
            meta.pop(integ_ops.CAMPO, None)
        path = ws.root / rel
        _write_doc(path, meta, corpo)
        reindex_file(ws, conn, path)

    # -- escritas do agente (change 0147) -----------------------------------
    #
    # Prévia e gravação em ROTAS SEPARADAS, não num `apply` no corpo: o log de
    # atividade registra o caminho, e um booleano no corpo não apareceria lá.
    # O registro precisa distinguir "o agente olhou" de "o agente gravou".

    @app.post(API_PREFIX + "/integrations/write/testcase/preview")
    async def mcp_preview_testcase(request: Request, payload: McpTestcaseIn):
        return mcp_write.previa_testcase(
            ws_of(request), conn_of(request), payload.model_dump())

    @app.post(API_PREFIX + "/integrations/write/testcase")
    async def mcp_write_testcase(request: Request, payload: McpTestcaseIn):
        ws, conn = ws_of(request), conn_of(request)
        resultado = mcp_write.aplicar_testcase(
            ws, conn, payload.model_dump(), author_of(request),
            _write_doc, reindex_file,
        )
        await asyncio.to_thread(
            versioning.commit_paths, ws, [ws.root / resultado["path"]],
            f"{resultado['action']} {resultado['entity_id']} via agente",
            author_of(request),
        )
        return resultado

    @app.post(API_PREFIX + "/integrations/write/result/preview")
    async def mcp_preview_result(request: Request, payload: McpResultIn):
        return mcp_write.previa_resultado(
            ws_of(request), conn_of(request), payload.model_dump(), exec_ops.load)

    @app.post(API_PREFIX + "/integrations/write/result")
    async def mcp_write_result(request: Request, payload: McpResultIn):
        return mcp_write.aplicar_resultado(
            ws_of(request), conn_of(request), payload.model_dump(),
            author_of(request), exec_ops, reindex_file,
        )

    @app.post(API_PREFIX + "/integrations/write/link/preview")
    async def mcp_preview_link(request: Request, payload: McpLinkIn):
        return mcp_write.previa_vinculo(
            ws_of(request), conn_of(request), payload.model_dump(),
            _find_path, _load_doc,
        )

    @app.post(API_PREFIX + "/integrations/write/link")
    async def mcp_write_link(request: Request, payload: McpLinkIn):
        return mcp_write.aplicar_vinculo(
            ws_of(request), conn_of(request), payload.model_dump(),
            _find_path, _load_doc, _write_doc, reindex_file,
        )

    # -- intercâmbio por arquivo (change 0148) ------------------------------
    #
    # O adaptador que funciona com QUALQUER ferramenta: toda ferramenta de
    # teste do mercado importa CSV, e nenhuma exige credencial para isso. É
    # também o SEGUNDO adaptador — e é ele que prova que a porta da change
    # 0145 não saiu com o formato de uma ferramenta só.

    @app.get(API_PREFIX + "/integrations/file/testcases")
    async def exportar_casos_csv(request: Request, system: str = "file",
                                 folder: str = ""):
        ws, conn = ws_of(request), conn_of(request)
        linhas = []
        for row in conn.execute("SELECT id, path FROM testcases ORDER BY id"):
            if folder and not row["path"].startswith(f"testcases/{folder}"):
                continue
            try:
                meta, corpo = _load_doc(ws, row["path"])
            except (OSError, ValueError):
                continue
            linhas.append({"meta": meta, "body": corpo})
        csv_texto = file_ops.exportar_casos(linhas, system)
        return Response(
            content=csv_texto, media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition":
                     'attachment; filename="arbites-testcases.csv"'},
        )

    @app.get(API_PREFIX + "/integrations/file/results")
    async def exportar_resultados_csv(request: Request, execution: str = "",
                                      system: str = "file"):
        ws, conn = ws_of(request), conn_of(request)
        ids = ([execution] if execution else
               [r["id"] for r in conn.execute(
                   "SELECT id FROM executions ORDER BY created_at DESC LIMIT 200")])
        execucoes = []
        for exec_id in ids:
            try:
                execucoes.append(exec_ops.load(ws, exec_id))
            except Exception:  # noqa: BLE001 — ciclo removido do disco
                continue
        csv_texto = file_ops.exportar_resultados(execucoes, system)
        return Response(
            content=csv_texto, media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition":
                     'attachment; filename="arbites-results.csv"'},
        )

    @app.post(API_PREFIX + "/integrations/file/testcases/preview")
    async def previa_import_casos(request: Request, payload: FileImportIn):
        ws, conn = ws_of(request), conn_of(request)
        linhas = file_ops.ler_csv(payload.content, ["title"])

        def achar(system: str, remote_id: str):
            achado = mcp_write.achar_por_vinculo(
                ws, conn, "testcases", system, remote_id)
            return achado[0] if achado else None

        return file_ops.previa_importacao(linhas, payload.system, achar)

    @app.post(API_PREFIX + "/integrations/file/testcases")
    async def importar_casos(request: Request, payload: FileImportIn):
        """Importa. A idempotência vem do `external_id`, não da ordem: o mesmo
        arquivo importado de novo ATUALIZA o que já entrou."""
        ws, conn = ws_of(request), conn_of(request)
        linhas = file_ops.ler_csv(payload.content, ["title"])

        def achar(system: str, remote_id: str):
            achado = mcp_write.achar_por_vinculo(
                ws, conn, "testcases", system, remote_id)
            return achado[0] if achado else None

        plano = file_ops.previa_importacao(linhas, payload.system, achar)
        ignoradas = {d["line"] for d in plano["skipped_duplicates"]}
        criados, atualizados = [], []
        for numero, linha in enumerate(linhas, start=2):
            if numero in ignoradas:
                continue
            pedido = {
                "title": (linha.get("title") or "").strip(),
                "body": linha.get("body") or "",
                "type": (linha.get("type") or "").strip() or None,
                "priority": (linha.get("priority") or "").strip() or None,
                "status": (linha.get("status") or "").strip() or None,
                "story": (linha.get("story") or "").strip() or None,
                "folder": (linha.get("folder") or "").strip() or None,
                "tags": [t for t in (linha.get("tags") or "").split(
                    file_ops.SEPARADOR_LISTA) if t.strip()] or None,
            }
            externo = (linha.get("external_id") or "").strip()
            if externo:
                pedido["system"] = payload.system
                pedido["remote_id"] = externo
            feito = mcp_write.aplicar_testcase(
                ws, conn, pedido, author_of(request), _write_doc, reindex_file)
            (criados if feito["action"] == "create" else atualizados).append(
                feito["entity_id"])
        return {"created": criados, "updated": atualizados, "plan": plano}

    @app.post(API_PREFIX + "/integrations/file/cucumber/preview")
    async def previa_cucumber(request: Request, payload: FileImportIn):
        """Os cenários do arquivo e a que caso cada um se liga pela tag."""
        cenarios = file_ops.ler_cucumber(payload.content)
        conn = conn_of(request)
        conhecidos, orfaos = [], []
        for cenario in cenarios:
            ct = cenario.get("testcase_id")
            existe = bool(ct) and conn.execute(
                "SELECT 1 FROM testcases WHERE id = ?", (ct,)).fetchone()
            (conhecidos if existe else orfaos).append(cenario)
        return {
            "scenarios": cenarios,
            "matched": conhecidos,
            "unmatched": orfaos,
            "warnings": (
                [f"{len(orfaos)} cenário(s) sem tag @CT-XXXX que resolva para um"
                 " caso daqui — sem a tag não há como ligar resultado a caso"
                 " (ADR 0003)"] if orfaos else []
            ),
        }

    # -- envio em lote (change 0150) ----------------------------------------
    #
    # O agente é a ponte certa para o fluxo com humano no meio e a ponte
    # ERRADA para volume: empurrar 47 resultados não deveria custar 47 turnos,
    # 47 confirmações, nem variar de uma execução para outra.

    def _lote_de(request: Request, system: str):
        return bulk_ops.Lote(
            ws_of(request), conn_of(request), bulk_ops.tracker_para(system),
            system, _load_doc, _write_doc, reindex_file,
        )

    @app.get(API_PREFIX + "/integrations/bulk/{exec_id}/preview")
    async def previa_lote(request: Request, exec_id: str, system: str = "file"):
        execution = exec_ops.load(ws_of(request), exec_id)
        return _lote_de(request, system).delta(execution)

    @app.post(API_PREFIX + "/integrations/bulk/{exec_id}")
    async def empurrar_lote(request: Request, exec_id: str, system: str = "file"):
        """Empurra o ciclo. Reexecutável sem efeito colateral: o que já foi
        tem vínculo, e o que tem vínculo sai do delta."""
        execution = exec_ops.load(ws_of(request), exec_id)
        return await _lote_de(request, system).empurrar(execution)

    @app.get(API_PREFIX + "/integrations/capabilities")
    async def integration_capabilities(request: Request):
        """O que cada adaptador consegue representar. O que ele NÃO representa
        precisa ser dito em voz alta antes de sincronizar, não descoberto
        depois (ADR 0015)."""
        return {"adapters": [c.as_dict() for c in integ_ops.ADAPTADORES.values()]}

    # -- credencial do agente (MCP, change 0146) ----------------------------

    @app.get(API_PREFIX + "/profile/agent-tokens")
    async def list_agent_tokens(request: Request):
        user = current_user(request)
        return {"tokens": auth_ops.list_agent_tokens(request.app.state.auth, user["id"])}

    @app.post(API_PREFIX + "/profile/agent-tokens", status_code=201)
    async def create_agent_token(request: Request, payload: AgentTokenIn):
        """Devolve o token EM CLARO uma única vez — depois só o hash existe."""
        user = current_user(request)
        raw, meta = auth_ops.create_agent_token(
            request.app.state.auth, user["id"], payload.name
        )
        return {"token": raw, **meta}

    @app.delete(API_PREFIX + "/profile/agent-tokens/{token_id}", status_code=204)
    async def revoke_agent_token(request: Request, token_id: str):
        user = current_user(request)
        if not auth_ops.revoke_agent_token(request.app.state.auth, user["id"], token_id):
            raise _error(404, "not_found", "credencial não encontrada")

    @app.get(API_PREFIX + "/settings/github/token")
    async def github_token_status(request: Request):
        # Status apenas, nunca o valor. A VALIDADE não é segredo — é uma data,
        # e existe para ser vista antes de passar (change 0157).
        credencial: CredentialState = request.app.state.credential
        tokens = request.app.state.tokens
        return credencial.status(
            tokens.get() is not None,
            gravavel=tokens.available(), origem=tokens.source(),
        )

    @app.put(API_PREFIX + "/settings/github/token")
    async def github_token_set(request: Request, payload: TokenIn):
        request.app.state.tokens.set(payload.token)
        # O provedor não conta ao cliente quando o token expira: quem o criou
        # informa. Sem isso o Arbites só descobre a expiração quando ela já
        # aconteceu — tarde demais para pedir a renovação a tempo.
        credencial: CredentialState = request.app.state.credential
        credencial.registrar_token(payload.expires_at)
        tokens = request.app.state.tokens
        return credencial.status(
            True, gravavel=tokens.available(), origem=tokens.source())

    # -- migração Xray (M2) -------------------------------------------------

    @app.post(API_PREFIX + "/import/xray")
    async def import_xray_preview(request: Request, file: UploadFile = File(...)):
        tests = xray_ops.parse_xray_xml(await file.read())
        return xray_ops.preview(conn_of(request), tests)

    @app.post(API_PREFIX + "/import/xray/confirm")
    async def import_xray_confirm(
        request: Request,
        file: UploadFile = File(...),
        folder: str = Form(default="xray"),
        create_stories: str = Form(default=""),
    ):
        ws, conn = ws_of(request), conn_of(request)
        tests = xray_ops.parse_xray_xml(await file.read())
        stories = [s.strip() for s in create_stories.split(",") if s.strip()]
        return xray_ops.confirm(
            ws,
            conn,
            tests,
            folder,
            stories,
            write_doc=_write_doc,
            reindex=lambda path: reindex_file(ws, conn, path),
        )

    @app.post(API_PREFIX + "/export/markdown")
    async def export_markdown(request: Request, folder: str = ""):
        import io
        import zipfile

        ws = ws_of(request)
        base = ws.root / "testcases"
        root = base / folder.strip("/") if folder.strip("/") else base
        if not root.exists():
            raise _error(404, "not_found", f"pasta não existe: {folder}")
        buffer = io.BytesIO()
        count = 0
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(root.rglob("*.md")):
                zf.write(path, path.relative_to(base).as_posix())
                count += 1
        if count == 0:
            raise _error(404, "empty", "nenhum .md na pasta")
        buffer.seek(0)
        return Response(
            content=buffer.read(),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="testcases.zip"'},
        )

    # -- IA opcional (M5) -----------------------------------------------------

    # -- perfil / memória de longo prazo (doc §2) ---------------------------

    def _legacy_profile_path(ws: Workspace) -> Path:
        return ws.root / "profile.md"

    def _account_slug(email: str) -> str:
        """Identidade de ARQUIVO de uma conta — unívoca, e ainda legível.

        `slugify` colapsa qualquer pontuacao no mesmo hifen, entao
        `ana.silva@x.com` e `ana-silva@x.com` dao o mesmo texto. Usar so ele
        faria duas contas distintas resolverem o mesmo caminho e
        compartilharem perfil, memoria de IA e avatar (change 0119).

        O slug fica na frente porque um workspace aberto no Obsidian precisa
        dizer de quem e cada arquivo; o sufixo vem do e-mail INTEIRO e e o
        que garante que duas contas nunca colidam.
        """
        digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()[:8]
        return f"{slugify(email)}-{digest}"

    def _adopt_legacy_name(directory: Path, slug: str, novo: str) -> None:
        """Adota o arquivo gravado sob o nome antigo (so o slug).

        Sem isto a atualizacao apagaria do mapa a memoria ja escrita: o
        arquivo continuaria no disco, mas ninguem mais o leria. Se duas
        contas colidiam, a primeira que ler adota — e a outra comeca limpa,
        que e exatamente o isolamento que faltava.
        """
        if slug == novo or not directory.is_dir():
            return
        for antigo in directory.glob(f"{slug}.*"):
            if not antigo.is_file():
                continue
            destino = directory / f"{novo}{antigo.suffix}"
            if not destino.exists():
                antigo.rename(destino)

    def _profile_path(request: Request) -> Path:
        """Perfil da conta logada.

        A memoria de longo prazo entra em TODA chamada de IA; compartilhar o
        arquivo faria a IA responder a um QA com o contexto de outro. Sem
        autenticacao (instalacao de uma pessoa so) segue o arquivo da raiz.
        """
        ws = ws_of(request)
        if not getattr(request.app.state, "auth_enabled", True):
            return _legacy_profile_path(ws)
        email = current_user(request)["email"]
        directory = ws.root / "profiles"
        nome = _account_slug(email)
        _adopt_legacy_name(directory, slugify(email), nome)
        return directory / f"{nome}.md"

    def _seed_profile(request: Request, path: Path) -> None:
        """Primeira leitura de uma conta: template, ou o `profile.md` da raiz
        para a conta de menor id — que e, por construcao, o usuario unico que
        existia antes de a instancia virar multiusuario."""
        legacy = _legacy_profile_path(ws_of(request))
        inherits = False
        if getattr(request.app.state, "auth_enabled", True) and legacy.exists():
            first = request.app.state.auth.execute(
                "SELECT MIN(id) AS id FROM users"
            ).fetchone()
            inherits = first is not None and first["id"] == current_user(request)["id"]
        if inherits:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
            legacy.unlink()  # herdado uma unica vez
        else:
            _write_doc(path, {"name": ""}, PROFILE_TEMPLATE)

    def _load_profile(request: Request) -> tuple[str, str]:
        ws = ws_of(request)
        path = _profile_path(request)
        if not path.exists():
            _seed_profile(request, path)
        meta, body = _load_doc(ws, ws.relpath(path))
        return str(meta.get("name") or ""), body


    # Assinatura de bytes, nao a extensao: um .png pode ser qualquer coisa, e
    # o avatar e servido de volta para o navegador.
    _IMAGE_SIGNATURES = (
        (bytes.fromhex("89504e470d0a1a0a"), "png"),
        (bytes.fromhex("ffd8ff"), "jpg"),
    )
    _AVATAR_MAX_BYTES = 1024 * 1024

    def _sniff_image(blob: bytes) -> str | None:
        for magic, ext in _IMAGE_SIGNATURES:
            if blob.startswith(magic):
                return ext
        if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
            return "webp"
        return None

    def _avatar_dir(request: Request) -> Path:
        return ws_of(request).root / "profiles" / "avatars"

    def _avatar_slug(request: Request) -> str:
        if not getattr(request.app.state, "auth_enabled", True):
            return "local"
        email = current_user(request)["email"]
        nome = _account_slug(email)
        _adopt_legacy_name(_avatar_dir(request), slugify(email), nome)
        return nome

    def _find_avatar(request: Request) -> Path | None:
        slug = _avatar_slug(request)
        for candidate in _avatar_dir(request).glob(f"{slug}.*"):
            if candidate.is_file():
                return candidate
        return None

    @app.get(API_PREFIX + "/profile/avatar")
    async def get_avatar(request: Request):
        path = _find_avatar(request)
        if path is None:
            # Sem imagem nao e erro: o cliente desenha o identicon.
            raise _error(404, "no_avatar", "esta conta nao tem imagem")
        # `private` porque a imagem e de UMA conta e esta instancia fica
        # atras de um tunel; `no-cache` para revalidar sempre, o que mantem
        # o ganho do ETag (304) sem servir a foto antiga depois da troca.
        return FileResponse(
            str(path), headers={"Cache-Control": "private, no-cache"}
        )

    @app.put(API_PREFIX + "/profile/avatar")
    async def put_avatar(request: Request, file: UploadFile = File(...)):
        blob = await file.read()
        if len(blob) > _AVATAR_MAX_BYTES:
            raise _error(422, "avatar_too_large",
                         "a imagem precisa ter no maximo 1 MB")
        ext = _sniff_image(blob)
        if ext is None:
            raise _error(422, "invalid_image",
                         "envie um PNG, JPEG ou WebP")
        directory = _avatar_dir(request)
        directory.mkdir(parents=True, exist_ok=True)
        for old in directory.glob(f"{_avatar_slug(request)}.*"):
            old.unlink()
        (directory / f"{_avatar_slug(request)}.{ext}").write_bytes(blob)
        return {"ok": True, "format": ext}

    @app.delete(API_PREFIX + "/profile/avatar", status_code=204)
    async def delete_avatar(request: Request):
        path = _find_avatar(request)
        if path is not None:
            path.unlink()
        return Response(status_code=204)

    @app.get(API_PREFIX + "/profile")
    async def get_profile(request: Request):
        name, memory = _load_profile(request)
        return {"name": name, "memory": memory}

    @app.put(API_PREFIX + "/profile")
    async def put_profile(request: Request, payload: ProfileIn):
        name, memory = _load_profile(request)
        if payload.name is not None:
            name = payload.name
        if payload.memory is not None:
            memory = payload.memory
        _write_doc(_profile_path(request), {"name": name or None}, memory)
        return {"name": name, "memory": memory}

    def _with_memory(request: Request, user_text: str) -> str:
        """Prefixa o conteúdo do usuário com a memória de longo prazo (doc §2).

        Injetado em TODA chamada de IA, independente do provider. Memória
        vazia/template intocado → sem bloco (prompt limpo).
        """
        try:
            _, memory = _load_profile(request)
        except OSError:
            return user_text
        stripped = memory.strip()
        if not stripped or stripped == PROFILE_TEMPLATE.strip():
            return user_text
        return (
            "Contexto persistente do usuário (memória de longo prazo):\n"
            f"{stripped}\n\n---\n\n{user_text}"
        )

    def _with_project_recap(request: Request, conn: sqlite3.Connection, user_text: str) -> str:
        """Empilha o recap de decisões/lições recentes (Memória Histórica do
        Projeto) sobre a memória de longo prazo do usuário — a IA "lembra"
        do que já aconteceu no projeto, não só do que o usuário escreveu no
        perfil."""
        recap = memory_ops.recent_recap(conn)
        text = f"{recap}\n\n---\n\n{user_text}" if recap else user_text
        return _with_memory(request, text)

    def _log_agent_event(
        ws: Workspace, conn: sqlite3.Connection, action: str,
        target_id: str | None, target_title: str | None, summary: str,
    ) -> None:
        """Registra uma interação de IA que gera/altera conteúdo — alimenta
        a linha do tempo da Memória Histórica do Projeto (`agent_log/`).

        Nunca levanta: neste ponto o LLM já respondeu, e uma falha ao gravar
        o log (disco, lock do índice) não pode custar ao usuário o conteúdo
        gerado — o log é acessório, a resposta é o produto.
        """
        try:
            event_id = ws.next_id("agent_event")
            meta = {
                "id": event_id,
                "at": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "target_id": target_id,
                "target_title": target_title,
            }
            path = ws.root / "agent_log" / f"{event_id}.md"
            _write_doc(path, meta, summary)
            reindex_file(ws, conn, path)
        except (OSError, sqlite3.Error) as exc:
            log.warning("agent_log falhou (resposta preservada): %s", exc)

    def _ai_config(ws: Workspace) -> dict:
        return ws.config().get("ai") or {"default_provider": None, "providers": []}

    def _ai_provider(request: Request, name: str | None):
        # Ponto unico por onde toda chamada de IA passa: o interruptor fica
        # aqui, e nao nas 7 rotas, para que uma rota nova ja nasca governada.
        require_switch(request, "ai")
        ws = ws_of(request)
        config = _ai_config(ws)
        chosen = name or config.get("default_provider")
        if not chosen:
            raise _error(409, "ai_disabled",
                         "nenhum provider de IA configurado (IA é opcional; "
                         "a plataforma segue 100% funcional)")
        for provider_cfg in config.get("providers") or []:
            if provider_cfg.get("name") == chosen:
                return ai_ops.build_provider(
                    provider_cfg, request.app.state.ai_keys,
                    transport=request.app.state.ai_transport,
                )
        raise _error(404, "not_found", f"provider '{chosen}' não configurado")

    def _providers_out(request: Request) -> dict:
        ws = ws_of(request)
        config = _ai_config(ws)
        keys: AIKeyStore = request.app.state.ai_keys
        return {
            "default_provider": config.get("default_provider"),
            "providers": [
                {
                    "name": p.get("name"),
                    "kind": p.get("kind"),
                    "model": p.get("model"),
                    "base_url": p.get("base_url"),
                    "key_configured": keys.configured(str(p.get("name"))),
                }
                for p in config.get("providers") or []
            ],
        }

    @app.get(API_PREFIX + "/ai/providers")
    async def get_ai_providers(request: Request):
        return _providers_out(request)

    @app.post(API_PREFIX + "/ai/providers/test")
    async def test_ai_provider(request: Request, payload: ProviderTestIn):
        """Chamada mínima ao provider (0085) — `{ok, error}`. Aceita um
        provider salvo (`name`) ou uma config inline (`kind`/`model`/
        `base_url`/`key`) ainda não persistida."""
        keys = request.app.state.ai_keys
        transport = request.app.state.ai_transport
        if payload.name and not payload.kind:
            config = _ai_config(ws_of(request))
            cfg = next((p for p in config.get("providers") or []
                        if p.get("name") == payload.name), None)
            if not cfg:
                raise _error(404, "not_found",
                             f"provider '{payload.name}' não configurado")
            provider = ai_ops.build_provider(cfg, keys, transport=transport)
        else:
            if not payload.kind:
                raise _error(422, "invalid_request",
                             "informe `name` (provider salvo) ou `kind`+`model` (inline)")
            name = payload.name or "__inline__"
            cfg = {"name": name, "kind": payload.kind,
                   "model": payload.model or "", "base_url": payload.base_url}
            eff_keys = _InlineKeys(keys, name, payload.key) if payload.key else keys
            provider = ai_ops.build_provider(cfg, eff_keys, transport=transport)
        ok, error = await asyncio.to_thread(ai_ops.test_provider, provider)
        return {"ok": ok, "error": error}

    @app.put(API_PREFIX + "/ai/providers")
    async def put_ai_providers(request: Request, payload: AIProvidersIn):
        ws = ws_of(request)
        import yaml as _yaml

        config = ws.config()
        config["ai"] = {
            "default_provider": payload.default_provider,
            "providers": [
                p.model_dump(exclude_none=True) for p in payload.providers
            ],
        }
        ws.config_path.write_text(
            _yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        keys: AIKeyStore = request.app.state.ai_keys
        for name, secret in payload.keys.items():
            keys.set(name, secret)  # keyring — nunca no YAML
        return _providers_out(request)

    def _preview_out(generated: ai_ops.GeneratedTestcases, extra: dict | None = None) -> dict:
        return {
            "preview": True,  # nada foi gravado; aceite = POST /testcases
            "testcases": [
                {**item.model_dump(), "body": ai_ops.testcase_body(item)}
                for item in generated.testcases
            ],
            **(extra or {}),
        }

    @app.post(API_PREFIX + "/ai/generate-testcases")
    async def ai_generate(request: Request, payload: GenerateIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        source = payload.source.strip()
        source_id, source_title = None, None
        if source.upper().startswith(("ST-", "EP-")) and len(source) < 32:
            source_id = source.upper()
            rel = _find_path(conn, "requirements", source_id)
            row = conn.execute(
                "SELECT title FROM requirements WHERE id = ?", (source_id,)
            ).fetchone()
            source_title = row["title"] if row else None
            source = (ws.root / rel).read_text(encoding="utf-8-sig")
        lessons = ai_ops.find_relevant_lessons(conn, source)
        lessons_used = [{"id": l["id"], "title": l["title"]} for l in lessons]

        # Geração POR CRITÉRIO (0093): story + critérios selecionados → um
        # prompt focado por critério, e o vínculo `criteria` já vem no
        # preview (o aceite grava story + criteria automaticamente).
        if source_id and payload.criteria:
            rows = conn.execute(
                "SELECT ears_id, text FROM criteria WHERE story_id = ?"
                f" AND ears_id IN ({','.join('?' * len(payload.criteria))})"
                " ORDER BY ord",
                [source_id, *payload.criteria],
            ).fetchall()
            if not rows:
                raise _error(422, "no_criteria",
                             "nenhum critério EARS informado existe nesta story")
            items: list[dict] = []
            for cr in rows:
                focus = (
                    f"{source}\n\n## Foco\nGere casos que validam ESPECIFICAMENTE"
                    f" o critério de aceite {cr['ears_id']}: {cr['text']}"
                )
                gen = await asyncio.to_thread(
                    ai_ops.generate_testcases, provider,
                    _with_project_recap(request, conn, focus), lessons,
                )
                for it in gen.testcases:
                    items.append({
                        **it.model_dump(), "body": ai_ops.testcase_body(it),
                        "criteria": [cr["ears_id"]],
                    })
            _log_agent_event(
                ws, conn, "generate_testcases", source_id, source_title,
                f"Gerou {len(items)} caso(s) por critério "
                f"({', '.join(r['ears_id'] for r in rows)}) para {source_id}",
            )
            return {"preview": True, "story": source_id, "testcases": items,
                    "lessons_used": lessons_used}

        generated = await asyncio.to_thread(
            ai_ops.generate_testcases, provider, _with_project_recap(request, conn, source), lessons
        )
        _log_agent_event(
            ws, conn, "generate_testcases", source_id, source_title,
            f"Gerou {len(generated.testcases)} caso(s) de teste"
            + (f" para {source_id}" if source_id else ""),
        )
        return _preview_out(generated, {"lessons_used": lessons_used})

    @app.post(API_PREFIX + "/ai/review/{ct_id}")
    async def ai_review(request: Request, ct_id: str, payload: AIByCtIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        rel = _find_path(conn, "testcases", ct_id)
        ct_md = (ws.root / rel).read_text(encoding="utf-8-sig")
        row = conn.execute(
            "SELECT title FROM testcases WHERE id = ?", (ct_id,)
        ).fetchone()
        tags = [
            r["tag"] for r in conn.execute(
                "SELECT tag FROM tc_tags WHERE testcase_id = ?", (ct_id,)
            )
        ]
        similar = ai_ops.find_similar(conn, row["title"], tags, exclude_id=ct_id)
        result = await asyncio.to_thread(
            ai_ops.review_testcase, provider, _with_project_recap(request, conn, ct_md), similar
        )
        _log_agent_event(
            ws, conn, "review_testcase", ct_id, row["title"] if row else None,
            f"Revisou {ct_id}: {len(result.issues)} issue(s) encontrado(s)",
        )
        return {"preview": True, "similar_considered": similar,
                **result.model_dump()}

    @app.post(API_PREFIX + "/ai/structure-lesson/{defect_id}")
    async def ai_structure_lesson(request: Request, defect_id: str, payload: AIByCtIn):
        """Sugere a lição estruturada (when/procedure/anti-pattern) a partir
        do defeito (0095) — preview: preenche o form, nada é gravado sem o
        save do defeito."""
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        rel = _find_path(conn, "defects", defect_id)
        defect_md = (ws.root / rel).read_text(encoding="utf-8-sig")
        result = await asyncio.to_thread(ai_ops.structure_lesson, provider, defect_md)
        return {"preview": True, **result.model_dump()}

    @app.post(API_PREFIX + "/ai/analyze-run/{exec_id}")
    async def ai_analyze_run(request: Request, exec_id: str, payload: AIByCtIn):
        """Resumo de falha pós-run (0096): junta os CTs failed/blocked da
        execution (erro + passos) e devolve resumo, causa provável e um draft
        de defeito — preview. O aceite é o `POST /defects` normal, já com
        `testcase`/`execution` preenchidos pelo cliente."""
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        try:
            execution = exec_ops.load(ws, exec_id)
        except (FileNotFoundError, OSError):
            raise _error(404, "not_found", f"{exec_id} não encontrado")
        failed = [
            r for r in execution.get("results", [])
            if r.get("status") in ("failed", "blocked")
        ]
        if not failed:
            raise _error(422, "no_failures",
                         "a execution não tem CTs failed/blocked para analisar")
        lines = [f"# Falha na execução {exec_id} — {execution.get('name', '')}", ""]
        first_ct = failed[0]["testcase_id"]
        for r in failed:
            row = conn.execute(
                "SELECT title FROM testcases WHERE id = ?", (r["testcase_id"],)
            ).fetchone()
            lines.append(f"## {r['testcase_id']} — {row['title'] if row else ''} "
                         f"({r['status']})")
            if r.get("error"):
                lines.append(f"Erro: {r['error']}")
            for st in r.get("steps", []):
                if st.get("status") in ("failed", "blocked"):
                    lines.append(f"- passo falho: {st.get('text', '')}")
            lines.append("")
        analysis = await asyncio.to_thread(
            ai_ops.analyze_run, provider, "\n".join(lines)
        )
        _log_agent_event(
            ws, conn, "analyze_run", exec_id, execution.get("name"),
            f"Analisou a falha de {exec_id}: {len(failed)} CT(s) com falha",
        )
        draft = analysis.defect.model_dump()
        draft["testcase"] = first_ct
        draft["execution"] = exec_id
        return {"preview": True, "summary": analysis.summary,
                "probable_cause": analysis.probable_cause, "defect": draft}

    @app.post(API_PREFIX + "/ai/negative-cases/{ct_id}")
    async def ai_negative(request: Request, ct_id: str, payload: AIByCtIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        rel = _find_path(conn, "testcases", ct_id)
        ct_md = (ws.root / rel).read_text(encoding="utf-8-sig")
        row = conn.execute(
            "SELECT title FROM testcases WHERE id = ?", (ct_id,)
        ).fetchone()
        generated = await asyncio.to_thread(
            ai_ops.negative_cases, provider, _with_memory(request, ct_md)
        )
        _log_agent_event(
            ws, conn, "negative_cases", ct_id, row["title"] if row else None,
            f"Gerou {len(generated.testcases)} caso(s) negativo(s) para {ct_id}",
        )
        return _preview_out(generated)

    @app.post(API_PREFIX + "/import/ai")
    async def import_ai_preview(
        request: Request, file: UploadFile = File(...), provider: str = Form(default="")
    ):
        """Importação inteligente (doc §1.1): txt/md/xml livre → CTs BDD em preview."""
        ws = ws_of(request)
        name = file.filename or "arquivo.txt"
        ext = Path(name).suffix.lower()
        if ext not in (".txt", ".md", ".xml"):
            raise _error(422, "invalid_file", "envie um arquivo .txt, .md ou .xml")
        text = (await file.read()).decode("utf-8", errors="replace")
        if not text.strip():
            raise _error(422, "empty_file", "arquivo vazio")

        # Arquivo já em Gherkin/BDD → preservar VERBATIM (sem IA, sem parafrasear,
        # sem exigir provider). Cada Scenario vira um CT com o corpo intacto.
        if ai_ops.looks_like_gherkin(text):
            scenarios = ai_ops.parse_gherkin(text)
            if scenarios:
                return {
                    "preview": True,
                    "folder": ai_ops.gherkin_folder(scenarios),
                    "testcases": [
                        {
                            "title": sc["title"],
                            "type": "manual",
                            "priority": "medium",
                            "tags": [],
                            "objetivo": "",
                            "pre_condicoes": [],
                            "passos": [],
                            "resultado_esperado": "",
                            "body": ai_ops.gherkin_body(sc),
                        }
                        for sc in scenarios
                    ],
                }

        prov = _ai_provider(request, provider or None)
        conversion = await asyncio.to_thread(
            ai_ops.convert_import, prov, name, _with_memory(request, text)
        )
        return {
            "preview": True,  # nada gravado; aceite = POST /testcases por item
            "folder": conversion.folder,
            "testcases": [
                {**item.model_dump(), "body": ai_ops.testcase_body_bdd(item)}
                for item in conversion.testcases
            ],
        }

    # -- defects (M1, mínimo) ---------------------------------------------

    def _defect_out(conn, ws: Workspace, defect_id: str) -> dict:
        row = conn.execute("SELECT * FROM defects WHERE id = ?", (defect_id,)).fetchone()
        if not row:
            raise _error(404, "not_found", f"{defect_id} não encontrado")
        out = dict(row)
        _, out["body"] = _load_doc(ws, row["path"])
        return out

    @app.get(API_PREFIX + "/defects")
    async def list_defects(
        request: Request, status: str = "", testcase: str = "", has_lesson: bool = False
    ):
        sql, params = "SELECT * FROM defects WHERE 1=1", []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if testcase:
            sql += " AND testcase_id = ?"
            params.append(testcase)
        if has_lesson:
            sql += " AND (root_cause IS NOT NULL OR fix IS NOT NULL OR prevention IS NOT NULL)"
        return [
            dict(r) for r in conn_of(request).execute(sql + " ORDER BY id", params)
        ]

    @app.post(API_PREFIX + "/defects", status_code=201)
    async def create_defect(request: Request, payload: DefectIn):
        ws, conn = ws_of(request), conn_of(request)
        defect_id = ws.next_id("defect")
        meta = {
            "id": defect_id,
            "title": payload.title,
            "status": payload.status,
            "severity": payload.severity,
            "testcase": payload.testcase,
            "execution": payload.execution,
            "external_key": payload.external_key,
            "opened": date.today().isoformat(),
            "created_by": author_of(request),
            "root_cause": payload.root_cause,
            "fix": payload.fix,
            "prevention": payload.prevention,
            "lesson_when": payload.lesson_when,
            "lesson_procedure": payload.lesson_procedure,
            "lesson_antipattern": payload.lesson_antipattern,
        }
        path = ws.root / "defects" / f"{defect_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body)
        reindex_file(ws, conn, path)
        if payload.execution and payload.testcase:
            execution = exec_ops.load(ws, payload.execution)
            exec_ops.link_defect(execution, payload.testcase, defect_id, author_of(request))
            _save_and_index(ws, conn, execution)
        return _defect_out(conn, ws, defect_id)

    @app.get(API_PREFIX + "/defects/{defect_id}")
    async def get_defect(request: Request, defect_id: str):
        return _defect_out(conn_of(request), ws_of(request), defect_id)

    @app.put(API_PREFIX + "/defects/{defect_id}")
    async def update_defect(request: Request, defect_id: str, payload: DefectUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "defects", defect_id)
        meta, body = _load_doc(ws, rel)
        changes = payload.model_dump(exclude_unset=True)
        body = changes.pop("body", body)
        meta.update(changes)
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        return _defect_out(conn, ws, defect_id)

    @app.delete(API_PREFIX + "/defects/{defect_id}", status_code=204)
    async def delete_defect(request: Request, defect_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "defects", defect_id)
        path = ws.root / rel
        ws.trash(path)
        reindex_file(ws, conn, path)

    # -- busca de entidades (autocomplete de links / menções @) -----------

    @app.get(API_PREFIX + "/search")
    async def search_entities(
        request: Request, q: str = "", limit: int = 20, kinds: str = ""
    ):
        conn = conn_of(request)
        like = f"%{q}%"
        wanted = {k for k in kinds.split(",") if k}
        sources = [
            ("testcase", "SELECT id, title FROM testcases"),
            ("requirement", "SELECT id, title FROM requirements"),
            ("execution", "SELECT id, name title FROM executions"),
            ("defect", "SELECT id, title FROM defects"),
            ("todo", "SELECT id, title FROM todos"),
            ("meeting", "SELECT id, title FROM meetings"),
            ("decision", "SELECT id, title FROM decisions"),
        ]
        out = []
        for kind, base in sources:
            if wanted and kind not in wanted:
                continue
            for r in conn.execute(
                base + " WHERE id LIKE ? OR title LIKE ? ORDER BY id LIMIT ?",
                (like, like, limit),
            ):
                out.append({"id": r["id"], "title": r["title"], "kind": kind})
        ql = q.lower()
        out.sort(key=lambda e: (not e["id"].lower().startswith(ql), e["id"]))
        return {"results": out[:limit]}

    # -- todos (M10) -------------------------------------------------------

    def _resolve_link(conn, link_id: str) -> dict:
        """Resolve o título de um artefato linkado (CT/execução/requisito)."""
        for table, kind, col in (
            ("testcases", "testcase", "title"),
            ("requirements", "requirement", "title"),
            ("executions", "execution", "name"),
            ("defects", "defect", "title"),
            ("decisions", "decision", "title"),
        ):
            row = conn.execute(
                f"SELECT {col} v FROM {table} WHERE id = ?", (link_id,)
            ).fetchone()
            if row:
                return {"id": link_id, "kind": kind, "title": row["v"]}
        return {"id": link_id, "kind": None, "title": None}  # link pendente

    def _linha_do_afazer(conn, todo_id: str) -> dict | None:
        """De que linha de lista este afazer participa.

        É CONSULTA, não um segundo dado: o vínculo mora só na linha (change
        0164). Guardá-lo também no afazer abriria a chance de os dois se
        contradizerem, e aí alguém teria de decidir qual está certo sem ter
        como.
        """
        linha = conn.execute(
            "SELECT i.list_id, i.item_id, i.text, i.done, l.title AS list_title,"
            " l.due AS list_due FROM todolist_items i"
            " JOIN todolists l ON l.id = i.list_id WHERE i.todo_id = ?",
            (todo_id,)).fetchone()
        return dict(linha) if linha else None

    def _todo_out(conn, ws: Workspace, todo_id: str) -> dict:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if not row:
            raise _error(404, "not_found", f"{todo_id} não encontrado")
        out = dict(row)
        link_ids = [x for x in (row["links"] or "").split(",") if x]
        out["links"] = [_resolve_link(conn, x) for x in link_ids]
        out["list_item"] = _linha_do_afazer(conn, todo_id)
        _, out["body"] = _load_doc(ws, row["path"])
        return out

    @app.get(API_PREFIX + "/todos")
    async def list_todos(
        request: Request,
        status: str = "",
        squad: str = "",
        due_from: str = "",
        due_to: str = "",
        link: str = "",
    ):
        conn = conn_of(request)
        sql, params = "SELECT * FROM todos WHERE 1=1", []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if squad:
            sql += " AND squad = ?"
            params.append(squad)
        if due_from:
            sql += " AND due >= ?"
            params.append(due_from)
        if due_to:
            sql += " AND due <= ?"
            params.append(due_to)
        if link:
            sql += " AND (',' || links || ',') LIKE ?"
            params.append(f"%,{link},%")
        # abertos por prazo primeiro; concluídos ao final
        sql += " ORDER BY CASE status WHEN 'done' THEN 1 ELSE 0 END, due IS NULL, due, id"
        out = []
        for row in conn.execute(sql, params):
            item = dict(row)
            link_ids = [x for x in (row["links"] or "").split(",") if x]
            item["links"] = [_resolve_link(conn, x) for x in link_ids]
            item["list_item"] = _linha_do_afazer(conn, row["id"])
            out.append(item)
        return out

    # -- listas de To Do (change 0164) --------------------------------------
    #
    # O afazer é a nota adesiva: uma coisa a fazer, com prazo e status. A lista
    # é o roteiro: passos que só fazem sentido juntos, com prazo DA LISTA. E é
    # isso que dá sentido ao vínculo — quando uma linha precisa de prazo, de
    # status e de aparecer no sino, ela se liga a um afazer: o afazer traz a
    # data, a linha traz o passo.

    def _lista_out(conn, ws: Workspace, list_id: str) -> dict:
        row = conn.execute(
            "SELECT * FROM todolists WHERE id = ?", (list_id,)).fetchone()
        if not row:
            raise _error(404, "not_found", f"{list_id} não encontrado")
        meta, corpo = list_ops.ler(ws, row["path"])
        itens = []
        for item in meta.get("items") or []:
            saida = dict(item)
            if item.get("todo"):
                # O afazer vinculado vem RESOLVIDO: a linha mostra o prazo e o
                # status dele sem quem lê precisar abrir outra tela.
                afazer = conn.execute(
                    "SELECT id, title, status, due FROM todos WHERE id = ?",
                    (item["todo"],)).fetchone()
                saida["todo_ref"] = dict(afazer) if afazer else None
            itens.append(saida)
        return {
            "id": row["id"], "title": row["title"], "status": row["status"],
            "due": row["due"], "created": row["created"], "path": row["path"],
            "items": itens, "progress": list_ops.progresso(itens), "body": corpo,
        }

    @app.get(API_PREFIX + "/todolists")
    async def listar_listas(request: Request, status: str = ""):
        ws, conn = ws_of(request), conn_of(request)
        sql = "SELECT id FROM todolists"
        args: list[Any] = []
        if status:
            sql += " WHERE status = ?"
            args.append(status)
        sql += " ORDER BY due IS NULL, due, id"
        return [_lista_out(conn, ws, r["id"]) for r in conn.execute(sql, args)]

    @app.post(API_PREFIX + "/todolists", status_code=201)
    async def criar_lista(request: Request, payload: TodoListIn):
        ws, conn = ws_of(request), conn_of(request)
        caminho, meta = list_ops.criar(ws, payload.title, payload.due, payload.body)
        reindex_file(ws, conn, caminho)
        return _lista_out(conn, ws, meta["id"])

    @app.get(API_PREFIX + "/todolists/{list_id}")
    async def obter_lista(request: Request, list_id: str):
        return _lista_out(conn_of(request), ws_of(request), list_id)

    @app.put(API_PREFIX + "/todolists/{list_id}")
    async def atualizar_lista(request: Request, list_id: str,
                              payload: TodoListUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "todolists", list_id)
        meta, corpo = list_ops.ler(ws, rel)
        mudancas = payload.model_dump(exclude_unset=True)
        corpo = mudancas.pop("body", corpo)
        meta.update({k: v for k, v in mudancas.items()})
        meta["updated"] = date.today().isoformat()
        list_ops.gravar(ws, ws.root / rel, meta, corpo)
        reindex_file(ws, conn, ws.root / rel)
        return _lista_out(conn, ws, list_id)

    @app.delete(API_PREFIX + "/todolists/{list_id}", status_code=204)
    async def excluir_lista(request: Request, list_id: str):
        ws, conn = ws_of(request), conn_of(request)
        caminho = ws.root / _find_path(conn, "todolists", list_id)
        ws.trash(caminho)
        reindex_file(ws, conn, caminho)

    @app.post(API_PREFIX + "/todolists/{list_id}/items", status_code=201)
    async def criar_item(request: Request, list_id: str, payload: TodoListItemIn):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "todolists", list_id)
        meta, corpo = list_ops.ler(ws, rel)
        novo_id = list_ops.proximo_item_id(meta)
        list_ops.validar_vinculo(conn, payload.todo, list_id, novo_id)
        meta["items"].append(list_ops.normalizar_item(
            {**payload.model_dump(), "id": novo_id}, len(meta["items"])))
        list_ops.gravar(ws, ws.root / rel, meta, corpo)
        reindex_file(ws, conn, ws.root / rel)
        return _lista_out(conn, ws, list_id)

    @app.put(API_PREFIX + "/todolists/{list_id}/items/{item_id}")
    async def atualizar_item(request: Request, list_id: str, item_id: str,
                             payload: TodoListItemUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "todolists", list_id)
        meta, corpo = list_ops.ler(ws, rel)
        alvo = next((i for i in meta["items"] if i["id"] == item_id), None)
        if alvo is None:
            raise _error(404, "not_found", f"linha {item_id} não existe em {list_id}")
        mudancas = payload.model_dump(exclude_unset=True)
        if "todo" in mudancas:
            list_ops.validar_vinculo(conn, mudancas["todo"], list_id, item_id)
        alvo.update(mudancas)
        list_ops.gravar(ws, ws.root / rel, meta, corpo)
        reindex_file(ws, conn, ws.root / rel)
        return _lista_out(conn, ws, list_id)

    @app.delete(API_PREFIX + "/todolists/{list_id}/items/{item_id}")
    async def excluir_item(request: Request, list_id: str, item_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "todolists", list_id)
        meta, corpo = list_ops.ler(ws, rel)
        antes = len(meta["items"])
        meta["items"] = [i for i in meta["items"] if i["id"] != item_id]
        if len(meta["items"]) == antes:
            raise _error(404, "not_found", f"linha {item_id} não existe em {list_id}")
        list_ops.gravar(ws, ws.root / rel, meta, corpo)
        reindex_file(ws, conn, ws.root / rel)
        return _lista_out(conn, ws, list_id)

    @app.get(API_PREFIX + "/todos/export")
    async def export_todos(
        request: Request,
        format: str = "md",
        status: str = "",
        squad: str = "",
        due_from: str = "",
        due_to: str = "",
        ids: str = "",
    ):
        ws, conn = ws_of(request), conn_of(request)
        if ids:
            id_list = [x for x in ids.split(",") if x]
            rows = [
                conn.execute("SELECT * FROM todos WHERE id = ?", (i,)).fetchone()
                for i in id_list
            ]
            rows = [r for r in rows if r]
        else:
            sql, params = "SELECT * FROM todos WHERE 1=1", []
            for field, value in (("status", status), ("squad", squad)):
                if value:
                    sql += f" AND {field} = ?"
                    params.append(value)
            if due_from:
                sql += " AND due >= ?"
                params.append(due_from)
            if due_to:
                sql += " AND due <= ?"
                params.append(due_to)
            rows = conn.execute(sql + " ORDER BY due IS NULL, due, id", params).fetchall()
        items = []
        for r in rows:
            _, body = _load_doc(ws, r["path"])
            items.append({**dict(r), "body": body})
        if format == "xml":
            return PlainTextResponse(
                _todos_xml(items),
                media_type="application/xml; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="afazeres.xml"'},
            )
        return PlainTextResponse(
            _todos_markdown(items),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="afazeres.md"'},
        )

    @app.post(API_PREFIX + "/todos", status_code=201)
    async def create_todo(request: Request, payload: TodoIn):
        ws, conn = ws_of(request), conn_of(request)
        todo_id = ws.next_id("todo")
        meta = {
            "id": todo_id,
            "title": payload.title,
            "status": payload.status,
            "due": payload.due,
            "squad": payload.squad,
            "links": payload.links or None,
            "created": date.today().isoformat(),
        }
        path = ws.root / "todos" / f"{todo_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body)
        reindex_file(ws, conn, path)
        return _todo_out(conn, ws, todo_id)

    @app.get(API_PREFIX + "/todos/{todo_id}")
    async def get_todo(request: Request, todo_id: str):
        return _todo_out(conn_of(request), ws_of(request), todo_id)

    @app.put(API_PREFIX + "/todos/{todo_id}")
    async def update_todo(request: Request, todo_id: str, payload: TodoUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "todos", todo_id)
        meta, body = _load_doc(ws, rel)
        changes = payload.model_dump(exclude_unset=True)
        body = changes.pop("body", body)
        for field in ("due", "squad", "links"):
            if field in changes and not changes[field]:
                meta.pop(field, None)
                changes.pop(field)
        meta.update(changes)
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        return _todo_out(conn, ws, todo_id)

    @app.delete(API_PREFIX + "/todos/{todo_id}", status_code=204)
    async def delete_todo(request: Request, todo_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "todos", todo_id)
        path = ws.root / rel
        ws.trash(path)
        reindex_file(ws, conn, path)

    # -- daily (M11) -------------------------------------------------------

    _DATE_RE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}$")

    def _check_date(day: str) -> str:
        if not _DATE_RE.match(day):
            raise _error(422, "invalid_date", "data deve ser AAAA-MM-DD")
        return day

    def _daily_path(ws: Workspace, day: str) -> Path:
        return ws.root / "dailies" / f"{day}.md"

    @app.post(API_PREFIX + "/metrics/snapshot")
    async def metrics_snapshot(request: Request):
        ws, conn = ws_of(request), conn_of(request)
        return daily_ops.save_snapshot(ws, conn)

    @app.get(API_PREFIX + "/daily/{day}/context")
    async def daily_context(request: Request, day: str):
        ws, conn = ws_of(request), conn_of(request)
        ctx = daily_ops.build_context(ws, conn, _check_date(day))
        return {**ctx, "markdown": daily_ops.context_markdown(ctx)}

    @app.post(API_PREFIX + "/daily/{day}/generate")
    async def daily_generate(request: Request, day: str, payload: DailyGenerateIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        ctx = daily_ops.build_context(ws, conn, _check_date(day))
        markdown = daily_ops.context_markdown(ctx)
        digest = await asyncio.to_thread(
            ai_ops.generate_daily, provider, _with_memory(request, markdown)
        )
        return {"preview": True, "date": day, **digest.model_dump(), "context_markdown": markdown}

    @app.get(API_PREFIX + "/dailies")
    async def list_dailies(request: Request):
        ws = ws_of(request)
        base = ws.root / "dailies"
        days = sorted(
            (p.stem for p in base.glob("*.md") if _DATE_RE.match(p.stem)), reverse=True
        ) if base.exists() else []
        return {"dailies": days}

    @app.get(API_PREFIX + "/daily/{day}")
    async def get_daily(request: Request, day: str):
        ws = ws_of(request)
        path = _daily_path(ws, _check_date(day))
        if not path.exists():
            raise _error(404, "not_found", f"daily {day} não existe")
        meta, body = _load_doc(ws, ws.relpath(path))
        return {"date": day, "action_items": meta.get("action_items") or [], "body": body}

    @app.put(API_PREFIX + "/daily/{day}")
    async def put_daily(request: Request, day: str, payload: DailyIn):
        ws = ws_of(request)
        _check_date(day)
        meta = {"date": day, "action_items": payload.action_items or None}
        _write_doc(_daily_path(ws, day), meta, payload.body)
        return {"date": day, "action_items": payload.action_items, "body": payload.body}

    # -- meetings / reuniões (M12) -----------------------------------------

    def _meeting_out(conn, ws: Workspace, meeting_id: str) -> dict:
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if not row:
            raise _error(404, "not_found", f"{meeting_id} não encontrada")
        out = dict(row)
        _, out["body"] = _load_doc(ws, row["path"])
        return out

    @app.get(API_PREFIX + "/meetings")
    async def list_meetings(request: Request, date: str = ""):
        conn = conn_of(request)
        sql, params = "SELECT * FROM meetings WHERE 1=1", []
        if date:
            sql += " AND date = ?"
            params.append(date)
        return [dict(r) for r in conn.execute(sql + " ORDER BY date DESC, id DESC", params)]

    @app.post(API_PREFIX + "/meetings", status_code=201)
    async def create_meeting(request: Request, payload: MeetingIn):
        ws, conn = ws_of(request), conn_of(request)
        meeting_id = ws.next_id("meeting")
        meta = {
            "id": meeting_id,
            "title": payload.title,
            "date": payload.date or date.today().isoformat(),
        }
        path = ws.root / "meetings" / f"{meeting_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body)
        reindex_file(ws, conn, path)
        return _meeting_out(conn, ws, meeting_id)

    @app.get(API_PREFIX + "/meetings/{meeting_id}")
    async def get_meeting(request: Request, meeting_id: str):
        return _meeting_out(conn_of(request), ws_of(request), meeting_id)

    @app.put(API_PREFIX + "/meetings/{meeting_id}")
    async def update_meeting(request: Request, meeting_id: str, payload: MeetingUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "meetings", meeting_id)
        meta, body = _load_doc(ws, rel)
        changes = payload.model_dump(exclude_unset=True)
        body = changes.pop("body", body)
        if "summary" in changes and not changes["summary"]:
            meta.pop("summary", None)
            changes.pop("summary")
        meta.update(changes)
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        return _meeting_out(conn, ws, meeting_id)

    @app.delete(API_PREFIX + "/meetings/{meeting_id}", status_code=204)
    async def delete_meeting(request: Request, meeting_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "meetings", meeting_id)
        path = ws.root / rel
        ws.trash(path)
        reindex_file(ws, conn, path)

    @app.post(API_PREFIX + "/meetings/{meeting_id}/summarize")
    async def summarize_meeting(request: Request, meeting_id: str, payload: MeetingSummarizeIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        rel = _find_path(conn, "meetings", meeting_id)
        _, body = _load_doc(ws, rel)
        if not body.strip():
            raise _error(422, "empty_meeting", "reunião sem descrição/transcrição para resumir")
        result = await asyncio.to_thread(
            ai_ops.summarize_meeting, provider, _with_memory(request, body)
        )
        return {"preview": True, "id": meeting_id, **result.model_dump()}

    def _converted_todos(conn, meeting_id: str) -> list[dict]:
        """Todos já criados a partir desta reunião (link no todo, 0097)."""
        rows = conn.execute(
            "SELECT id, title, status FROM todos"
            " WHERE ',' || COALESCE(links, '') || ',' LIKE ?"
            " ORDER BY id",
            (f"%,{meeting_id},%",),
        ).fetchall()
        return [dict(r) for r in rows]

    @app.get(API_PREFIX + "/meetings/{meeting_id}/action-items")
    async def meeting_action_items(request: Request, meeting_id: str):
        """Preview determinístico (linhas `- [ ]`) + histórico dos afazeres
        já convertidos. Funciona sem nenhum provider de IA (0097)."""
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "meetings", meeting_id)
        _, body = _load_doc(ws, rel)
        return {
            "id": meeting_id,
            "deterministic": daily_ops.extract_action_items(body),
            "converted": _converted_todos(conn, meeting_id),
        }

    @app.post(API_PREFIX + "/meetings/{meeting_id}/action-items/generate")
    async def meeting_action_items_generate(
        request: Request, meeting_id: str, payload: MeetingActionItemsGenerateIn
    ):
        """Extração assistida por IA (preview), mesmo padrão da daily — usa o
        `summarize_meeting` e devolve os action items para revisão."""
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        rel = _find_path(conn, "meetings", meeting_id)
        _, body = _load_doc(ws, rel)
        if not body.strip():
            raise _error(422, "empty_meeting",
                         "reunião sem descrição/transcrição para extrair")
        result = await asyncio.to_thread(
            ai_ops.summarize_meeting, provider, _with_memory(request, body)
        )
        return {"preview": True, "id": meeting_id, "action_items": result.action_items}

    @app.post(
        API_PREFIX + "/meetings/{meeting_id}/action-items/accept", status_code=201
    )
    async def meeting_action_items_accept(
        request: Request, meeting_id: str, payload: MeetingActionItemsAcceptIn
    ):
        """Cria um afazer por item selecionado, vinculado à reunião (0097)."""
        ws, conn = ws_of(request), conn_of(request)
        _find_path(conn, "meetings", meeting_id)  # 404 se a reunião não existe
        created: list[str] = []
        for title in payload.items:
            title = title.strip()
            if not title:
                continue
            todo_id = ws.next_id("todo")
            meta = {
                "id": todo_id,
                "title": title,
                "status": "open",
                "links": [meeting_id],
                "created": date.today().isoformat(),
            }
            path = ws.root / "todos" / f"{todo_id}-{slugify(title)}.md"
            _write_doc(path, meta, "")
            reindex_file(ws, conn, path)
            created.append(todo_id)
        return {"created": created, "converted": _converted_todos(conn, meeting_id)}

    # -- decisions / decisões arquiteturais (Memória Histórica) -------------
    # Ponteiro + metadados do TIME DE QA sobre o projeto sob teste — não é
    # o sistema de ADR do próprio Doctrina (.doctrina/decisions/), que é meta
    # do framework e nunca é tocado por estas rotas.

    def _decision_out(conn, ws: Workspace, decision_id: str) -> dict:
        row = conn.execute(
            "SELECT * FROM decisions WHERE id = ?", (decision_id,)
        ).fetchone()
        if not row:
            raise _error(404, "not_found", f"{decision_id} não encontrada")
        out = dict(row)
        out["tags"] = [t for t in (row["tags"] or "").split(",") if t]
        _, out["body"] = _load_doc(ws, row["path"])
        return out

    @app.get(API_PREFIX + "/decisions")
    async def list_decisions(request: Request, status: str = "", squad: str = ""):
        conn = conn_of(request)
        sql, params = "SELECT * FROM decisions WHERE 1=1", []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if squad:
            sql += " AND squad = ?"
            params.append(squad)
        rows = conn.execute(sql + " ORDER BY created DESC, id DESC", params)
        return [
            {**dict(r), "tags": [t for t in (r["tags"] or "").split(",") if t]}
            for r in rows
        ]

    @app.post(API_PREFIX + "/decisions", status_code=201)
    async def create_decision(request: Request, payload: DecisionIn):
        ws, conn = ws_of(request), conn_of(request)
        decision_id = ws.next_id("decision")
        meta = {
            "id": decision_id,
            "title": payload.title,
            "status": payload.status,
            "squad": payload.squad,
            "tags": payload.tags or None,
            "supersedes": payload.supersedes,
            "created": date.today().isoformat(),
        }
        path = ws.root / "decisions" / f"{decision_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body if payload.body is not None else DEFAULT_DECISION_BODY)
        reindex_file(ws, conn, path)
        return _decision_out(conn, ws, decision_id)

    @app.get(API_PREFIX + "/decisions/{decision_id}")
    async def get_decision(request: Request, decision_id: str):
        return _decision_out(conn_of(request), ws_of(request), decision_id)

    @app.put(API_PREFIX + "/decisions/{decision_id}")
    async def update_decision(request: Request, decision_id: str, payload: DecisionUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "decisions", decision_id)
        meta, body = _load_doc(ws, rel)
        changes = payload.model_dump(exclude_unset=True)
        body = changes.pop("body", body)
        if "tags" in changes and not changes["tags"]:
            meta.pop("tags", None)
            changes.pop("tags")
        meta.update(changes)
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        return _decision_out(conn, ws, decision_id)

    @app.delete(API_PREFIX + "/decisions/{decision_id}", status_code=204)
    async def delete_decision(request: Request, decision_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "decisions", decision_id)
        path = ws.root / rel
        ws.trash(path)
        reindex_file(ws, conn, path)

    # -- audit / Agente Auditor ----------------------------------------
    # Consolida sinais que já existem no índice (warnings de indexação,
    # stories sem CT, defeitos abertos há muito tempo, automação quebrada)
    # num snapshot datado. Sem daemon: roda sob demanda (POST /audit/run) ou
    # "lazy" — GET /audit/latest dispara uma rodada nova quando a última
    # passou de `audit.auto_interval_hours` (default 24h) no arbites.yaml.

    def _audit_out(conn: sqlite3.Connection, ws: Workspace, audit_id: str) -> dict:
        row = conn.execute("SELECT * FROM audits WHERE id = ?", (audit_id,)).fetchone()
        if not row:
            raise _error(404, "not_found", f"{audit_id} não encontrada")
        meta, _ = _load_doc(ws, row["path"])
        return {
            "id": row["id"],
            "ran_at": row["ran_at"],
            "trigger": row["trigger"],
            "total": row["total"],
            "by_severity": json.loads(row["by_severity"] or "{}"),
            "by_category": json.loads(row["by_category"] or "{}"),
            "findings": meta.get("findings") or [],
        }

    def _run_audit(request: Request, trigger: str) -> dict:
        ws, conn = ws_of(request), conn_of(request)
        full_cfg = ws.config()
        cfg = full_cfg.get("audit") or {}
        pattern = (full_cfg.get("ci_monitoring") or {}).get("name_pattern")
        findings = audit_ops.collect_findings(
            conn, cfg.get("defect_aging_days"), cfg.get("broken_automation_days"),
            pattern,
        )
        summary = audit_ops.summarize(findings)
        audit_id = ws.next_id("audit")
        meta = {
            "id": audit_id,
            "ran_at": datetime.now(timezone.utc).isoformat(),
            "trigger": trigger,
            "total": summary["total"],
            "by_severity": summary["by_severity"],
            "by_category": summary["by_category"],
            "findings": findings,
        }
        path = ws.root / "audits" / f"{audit_id}.md"
        _write_doc(path, meta, audit_ops.audit_markdown(findings, summary))
        reindex_file(ws, conn, path)
        return _audit_out(conn, ws, audit_id)

    @app.post(API_PREFIX + "/audit/run", status_code=201)
    async def run_audit_now(request: Request):
        return _run_audit(request, "manual")

    @app.get(API_PREFIX + "/audit/latest")
    async def audit_latest(request: Request):
        ws, conn = ws_of(request), conn_of(request)
        cfg = ws.config().get("audit") or {}
        interval_hours = cfg.get("auto_interval_hours", 24)
        row = conn.execute(
            "SELECT id, ran_at FROM audits ORDER BY ran_at DESC LIMIT 1"
        ).fetchone()
        stale = True
        if row and row["ran_at"]:
            try:
                last = datetime.fromisoformat(row["ran_at"])
                stale = (
                    datetime.now(timezone.utc) - last
                ).total_seconds() > interval_hours * 3600
            except ValueError:
                stale = True
        if stale:
            return _run_audit(request, "auto")
        return _audit_out(conn, ws, row["id"])

    @app.get(API_PREFIX + "/audit/history")
    async def audit_history(request: Request, limit: int = 20):
        conn = conn_of(request)
        rows = conn.execute(
            "SELECT id, ran_at, trigger, total, by_severity, by_category"
            " FROM audits ORDER BY ran_at DESC LIMIT ?",
            (max(1, min(limit, 200)),),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "ran_at": r["ran_at"],
                "trigger": r["trigger"],
                "total": r["total"],
                "by_severity": json.loads(r["by_severity"] or "{}"),
                "by_category": json.loads(r["by_category"] or "{}"),
            }
            for r in rows
        ]

    @app.delete(API_PREFIX + "/audit/{audit_id}", status_code=204)
    async def delete_audit(request: Request, audit_id: str):
        """Exclui UMA rodada, para a lixeira (change 0151).

        Uma rodada é um documento do workspace como outro qualquer, e todos
        os outros já tinham exclusão. Vai para `.arbites/trash/` e não some:
        um retrato do estado de qualidade apagado sem volta não se
        recupera."""
        ws, conn = ws_of(request), conn_of(request)
        row = conn.execute(
            "SELECT path FROM audits WHERE id = ?", (audit_id,)
        ).fetchone()
        if not row:
            raise _error(404, "not_found", f"{audit_id} não encontrada")
        path = ws.root / row["path"]
        ws.trash(path)
        reindex_file(ws, conn, path)

    @app.delete(API_PREFIX + "/audit", status_code=200)
    async def delete_audits_before(request: Request, before: str = ""):
        """Exclui em lote as rodadas ANTERIORES a uma data (change 0151).

        `GET /audit/latest` dispara rodada nova sempre que a última passou do
        intervalo, então basta abrir a aba todo dia para a pasta crescer sem
        ninguém pedir. Exclusão de uma em uma não dá conta disso.

        Comparação por prefixo de data ISO, não por parse: `ran_at` é gravado
        em ISO UTC e ordenar string ISO é ordenar tempo. `before` é
        EXCLUSIVO — a rodada exatamente da data informada não é levada."""
        if not before:
            raise _error(422, "before_required",
                         "informe `before` (data ISO) — a exclusão em lote"
                         " não apaga o histórico inteiro sem recorte")
        ws, conn = ws_of(request), conn_of(request)
        rows = conn.execute(
            "SELECT id, path FROM audits WHERE ran_at < ? ORDER BY ran_at",
            (before,),
        ).fetchall()
        removed = []
        for row in rows:
            path = ws.root / row["path"]
            if path.exists():
                ws.trash(path)
                reindex_file(ws, conn, path)
            removed.append(row["id"])
        return {"removed": removed, "count": len(removed)}

    @app.get(API_PREFIX + "/audit/{audit_id}")
    async def get_audit(request: Request, audit_id: str):
        return _audit_out(conn_of(request), ws_of(request), audit_id)

    # -- memory / Memória Histórica do Projeto --------------------------
    # Linha do tempo cronológica (estilo git log) cruzando requisitos,
    # defeitos, lições aprendidas, decisões arquiteturais e interações de
    # agentes de IA — nada persistido além de `agent_events` (ver
    # `_log_agent_event`); o resto é derivado do que já está no índice.

    @app.get(API_PREFIX + "/memory/timeline")
    async def get_memory_timeline(
        request: Request,
        kinds: str = "",
        limit: int = 50,
        date_from: str = "",
        date_to: str = "",
    ):
        wanted = [k for k in kinds.split(",") if k] or None
        return memory_ops.timeline(
            conn_of(request), wanted, max(1, min(limit, 200)),
            date_from or None, date_to or None,
        )

    @app.get(API_PREFIX + "/memory/timeline/years")
    async def get_memory_timeline_years(request: Request, kinds: str = ""):
        wanted = [k for k in kinds.split(",") if k] or None
        return memory_ops.timeline_years(conn_of(request), wanted)



# ---------------------------------------------------------------------------
# Autenticacao (capability auth) — rotas /auth/* e o gate de sessao


class RegisterIn(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class PasswordIn(BaseModel):
    current_password: str
    new_password: str


class SwitchIn(BaseModel):
    enabled: bool

class ApproveIn(BaseModel):
    role: str = "viewer"


class RoleIn(BaseModel):
    role: str


class ResetIn(BaseModel):
    password: str



# Rotas que respondem sem sessao. Tudo o mais sob API_PREFIX exige cookie.
_PUBLIC_PATHS = {
    API_PREFIX + "/auth/login",
    API_PREFIX + "/auth/register",
    API_PREFIX + "/auth/me",
    API_PREFIX + "/health",
}

# Com must_change_password a sessao existe mas so serve para trocar a senha.
_PASSWORD_CHANGE_PATHS = {
    API_PREFIX + "/auth/password",
    API_PREFIX + "/auth/logout",
    API_PREFIX + "/auth/me",
}


def client_ip(request: Request) -> str:
    """IP real atras de tunel/proxy: Cloudflare primeiro, depois o primeiro
    salto do X-Forwarded-For, e so entao o socket (que seria sempre o proxy)."""
    cf = request.headers.get("cf-connecting-ip", "").strip()
    if cf:
        return cf
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded.strip():
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        auth_ops.SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
        max_age=int(auth_ops.ABSOLUTE_TIMEOUT.total_seconds()),
    )


def current_user(request: Request) -> dict[str, Any]:
    """Usuario da sessao. Fora do gate (ARBITES_AUTH=off) devolve um
    operador local sintetico, para que o resto do codigo nao precise de
    ramificacao."""
    user = getattr(request.state, "user", None)
    if user is not None:
        return user
    if not getattr(request.app.state, "auth_enabled", True):
        return {"id": 0, "email": "local", "name": "local", "role": "admin",
                "status": "active", "must_change_password": False,
                "created_at": None, "last_login_at": None}
    raise _error(401, "unauthenticated", "sessao necessaria")


# Superficies governadas: papel exigido e interruptor, numa tabela unica e
# auditavel. Fica no gate, e nao no corpo dos handlers, porque a validacao de
# parametros do FastAPI roda antes do handler — um 422 na frente do 403
# entregaria de graca a forma da rota a quem nao pode alcanca-la.
#
# (regex do caminho, metodos, papel exigido, interruptor)
_GOVERNED: tuple[tuple[str, set[str], str | None, str | None], ...] = (
    # Define o executavel e o cwd do subprocess: e o caminho real para
    # executar codigo no servidor (runner.py).
    (r"/targets$", {"PUT"}, "admin", None),
    (r"/targets/[^/]+/env$", {"GET", "PUT"}, "admin", "target_env"),
    (r"/env/catalog$", {"GET"}, "admin", "target_env"),
    (r"/automation/browse-features$", {"GET"}, "admin", "filesystem_browse"),
    (r"/settings/github/token$", {"PUT"}, "admin", None),
    (r"/ai/providers$", {"PUT"}, "admin", None),
    (r"/import/xray", {"POST"}, "admin", "xray_import"),
    (r"/runs/local$", {"POST"}, None, "local_runner"),
    # O painel inteiro, e nao rota a rota: uma rota /admin/ nova ja nasce
    # restrita. GET /admin/switches e a excecao deliberada — a UI precisa
    # saber o que esconder, e o estado de um interruptor nao e segredo.
    # Excluir rodada de auditoria e mais perto de destruir registro do que de
    # descartar rascunho: e um retrato do estado de qualidade num momento
    # (0151). Rodar e ler continuam abertos a qualquer papel.
    # Aplicar retenção remove anexo e run: é destrutivo, mesmo indo para a
    # lixeira. LER a prévia continua aberto — ver o que seria removido é o
    # que permite alguém discordar antes de acontecer.
    (r"/ci/retention/apply$", {"POST"}, "admin", None),
    # Declarar de onde a observabilidade puxa é escrever no arbites.yaml, o
    # mesmo alcance de PUT /targets e PUT /ai/providers. LER continua aberto:
    # a tela precisa dizer "nenhuma origem declarada" a quem não é admin.
    (r"/ci/sources$", {"PUT"}, "admin", None),
    (r"/audit$", {"DELETE"}, "admin", None),
    (r"/audit/[^/]+$", {"DELETE"}, "admin", None),
    (r"/admin/(?!switches$)", {"GET", "POST", "PUT", "DELETE"}, "admin", None),
    (r"/admin/switches$", {"PUT"}, "admin", None),
)

# Cada MÓDULO (ADR 0014) governa os caminhos que só ele usa, em todos os
# métodos. Gerado do registro em vez de escrito à mão: módulo novo nasce
# bloqueável sem ninguém lembrar de vir aqui — e, mais importante, o que a UI
# esconde e o que o servidor recusa saem da MESMA lista, então não têm como
# divergir.
_MODULE_GOVERNED: tuple[tuple[str, set[str], str | None, str | None], ...] = tuple(
    (re.escape(path), {"GET", "POST", "PUT", "PATCH", "DELETE"}, None, name)
    for name, spec in auth_ops.MODULES.items()
    for path in spec["paths"]
)

_GOVERNED_COMPILED = tuple(
    (re.compile("^" + API_PREFIX + pattern), methods, role, switch)
    for pattern, methods, role, switch in _GOVERNED + _MODULE_GOVERNED
)


def governed_for(path: str, method: str) -> tuple[str | None, str | None]:
    """Papel e interruptor exigidos por este caminho, se houver."""
    for matcher, methods, role, switch in _GOVERNED_COMPILED:
        if method in methods and matcher.match(path):
            return role, switch
    return None, None


# Escritas que um `viewer` pode fazer: as que agem sobre a propria conta.
_VIEWER_WRITABLE = {
    API_PREFIX + "/auth/password",
    API_PREFIX + "/auth/logout",
    API_PREFIX + "/auth/login",
    API_PREFIX + "/auth/register",
}


def require_role(request: Request, *roles: str) -> dict[str, Any]:
    """Exige um dos papeis. 403 e nao 404: esconder a existencia da rota nao
    protege nada e transforma autorizacao em adivinhacao."""
    user = current_user(request)
    if user["role"] not in roles:
        raise _error(
            403, "forbidden",
            "esta operacao exige papel %s" % " ou ".join(roles),
        )
    return user


def require_switch(request: Request, name: str) -> None:
    """Recusa a rota quando o admin desligou a capacidade correspondente."""
    if not getattr(request.app.state, "auth_enabled", True):
        return
    if not auth_ops.switch_enabled(request.app.state.auth, name):
        raise _error(
            403, "feature_disabled",
            "recurso desligado pelo administrador (interruptor '%s')" % name,
        )


def _register_auth(app: FastAPI) -> None:
    def auth_of(request: Request):
        return request.app.state.auth

    def ws_of(request: Request) -> Workspace:
        return request.app.state.ws

    def conn_of(request: Request) -> sqlite3.Connection:
        return request.app.state.conn

    @app.middleware("http")
    async def _session_gate(request: Request, call_next):
        path = request.url.path
        if not path.startswith(API_PREFIX) or not request.app.state.auth_enabled:
            return await call_next(request)
        raw = request.cookies.get(auth_ops.SESSION_COOKIE)
        user = auth_ops.resolve_session(request.app.state.auth, raw)
        # Credencial do agente (MCP, change 0146): um Bearer vale como sessão,
        # mas NÃO é a sessão — é outra credencial, revogável sozinha. O agente
        # entra pelo mesmo gate que todo mundo e herda o papel da conta dona,
        # então papel, módulo desligado e log de atividade valem sem regra
        # nova (ADR 0014/0015).
        if user is None:
            header = request.headers.get("authorization") or ""
            if header.lower().startswith("bearer "):
                # O interruptor `mcp_server` desliga a superfície do agente
                # INTEIRA (change 0149): sem ele a credencial não resolve, e
                # o navegador segue intacto — são credenciais diferentes.
                if auth_ops.switch_enabled(request.app.state.auth, "mcp_server"):
                    user = auth_ops.resolve_agent_token(
                        request.app.state.auth, header[7:].strip()
                    )
                    if user is not None:
                        request.state.via_agent = True
        request.state.user = user
        if path in _PUBLIC_PATHS:
            return await call_next(request)
        if user is None:
            response = JSONResponse(
                status_code=401,
                content={"error": {"code": "unauthenticated",
                                   "message": "sessao necessaria"}},
            )
            response.delete_cookie(auth_ops.SESSION_COOKIE, path="/")
            return response
        # "Ele mexe ou só olha?" é UMA pergunta com duas respostas — por isso
        # um interruptor, e não um por ferramenta (change 0149). Vale para
        # qualquer método que altere, inclusive os que ainda não existem.
        if (getattr(request.state, "via_agent", False)
                and request.method not in ("GET", "HEAD", "OPTIONS")
                and not auth_ops.switch_enabled(request.app.state.auth, "mcp_write")):
            return JSONResponse(
                status_code=403,
                content={"error": {
                    "code": "agent_write_disabled",
                    "message": "o agente está em modo somente-leitura;"
                               " ligue a escrita em IA → MCP",
                }},
            )
        if user["must_change_password"] and path not in _PASSWORD_CHANGE_PATHS:
            return JSONResponse(
                status_code=403,
                content={"error": {"code": "password_change_required",
                                   "message": "troque a senha antes de continuar"}},
            )
        # Recusa de escrita para `viewer` aqui, e nao rota a rota: uma rota
        # nova nasce protegida sem ninguem precisar lembrar de anota-la.
        if (user["role"] == "viewer"
                and request.method not in ("GET", "HEAD", "OPTIONS")
                and path not in _VIEWER_WRITABLE):
            return JSONResponse(
                status_code=403,
                content={"error": {"code": "forbidden",
                                   "message": "papel viewer nao pode escrever"}},
            )
        role, switch = governed_for(path, request.method)
        if role is not None and user["role"] != role:
            return JSONResponse(
                status_code=403,
                content={"error": {"code": "forbidden",
                                   "message": "esta operacao exige papel %s" % role}},
            )
        if switch is not None and not auth_ops.switch_enabled(
                request.app.state.auth, switch):
            return JSONResponse(
                status_code=403,
                content={"error": {
                    "code": "feature_disabled",
                    "message": "recurso desligado pelo administrador"
                               " (interruptor '%s')" % switch}},
            )
        response = await call_next(request)
        # Log de atividade aqui, e nao rota a rota: uma rota de escrita nova
        # entra no registro sozinha. Nada de corpo — caminho e metodo bastam,
        # e o corpo levaria senha e token para um registro que ninguem apaga.
        if (request.method not in ("GET", "HEAD", "OPTIONS")
                and response.status_code < 400
                and not path.startswith(API_PREFIX + "/auth/")):
            auth_ops.record_activity(
                request.app.state.auth, user, request.method, path,
                response.status_code, client_ip(request),
            )
        return response

    @app.get(API_PREFIX + "/health")
    async def health():
        # Qual CÓDIGO está rodando, não só qual versão do pacote (change
        # 0184): "atualizei e o erro continua" tem duas leituras, e sem isto
        # não havia como separar "não funcionou" de "não está rodando".
        return {"status": "ok", "version": __version__, **versao_ops.identidade()}

    @app.post(API_PREFIX + "/auth/register", status_code=201)
    async def register(request: Request, payload: RegisterIn):
        if os.environ.get("ARBITES_SIGNUP", "on").strip().lower() == "off":
            raise _error(403, "signup_disabled", "cadastro fechado nesta instancia")
        conn = auth_of(request)
        # Cadastro pendente numa instancia SEM admin ativo e um beco sem
        # saida: nao existe quem aprove. Quando o e-mail e o que o operador
        # declarou no ambiente, a conta ja nasce dona (change 0168).
        dono = auth_ops.claims_instance(conn, payload.email)
        user = auth_ops.create_user(
            conn, payload.email, payload.password, payload.name,
            role="admin" if dono else "viewer",
            status="active" if dono else "pending",
        )
        if dono:
            # Senha escolhida por quem se cadastrou, nao vinda do ambiente:
            # nao ha nada para trocar no primeiro login.
            return {"user": user, "admin": True,
                    "message": "primeira conta desta instancia;"
                               " entrou como administrador"}
        # Nasce pendente: nenhuma sessao aqui, de proposito.
        return {"user": user, "admin": False,
                "message": "cadastro recebido; aguarde a liberacao"}

    @app.post(API_PREFIX + "/auth/login")
    async def login(request: Request, payload: LoginIn):
        conn = auth_of(request)
        user = auth_ops.authenticate(
            conn, payload.email, payload.password, client_ip(request),
            request.headers.get("user-agent", ""),
        )
        token = auth_ops.open_session(
            conn, user["id"], client_ip(request),
            request.headers.get("user-agent", ""),
        )
        response = JSONResponse({"user": auth_ops.get_user(conn, user["id"])})
        _set_session_cookie(response, request, token)
        return response

    @app.post(API_PREFIX + "/auth/logout")
    async def logout(request: Request):
        auth_ops.revoke_session(
            auth_of(request), request.cookies.get(auth_ops.SESSION_COOKIE)
        )
        response = JSONResponse({"ok": True})
        response.delete_cookie(auth_ops.SESSION_COOKIE, path="/")
        return response

    @app.get(API_PREFIX + "/auth/me")
    async def me(request: Request):
        if not request.app.state.auth_enabled:
            return {"user": current_user(request), "auth_enabled": False}
        user = getattr(request.state, "user", None)
        # `no_admin` conta a quem ainda nao entrou que um cadastro feito
        # agora ficaria pendente para sempre, e `owner_declared` diz qual das
        # duas saidas serve (cadastrar-se com o e-mail do ambiente, ou o
        # comando local). E uma revelacao deliberada: ver ADR 0018.
        sem_admin = auth_ops.no_active_admin(auth_of(request))
        return {"user": user, "auth_enabled": True,
                "signup_enabled":
                    os.environ.get("ARBITES_SIGNUP", "on").strip().lower() != "off",
                "no_admin": sem_admin,
                "owner_declared":
                    bool(sem_admin and auth_ops.owner_email_from_env())}


    # -- painel de administracao (capability admin) -------------------------

    def _target_user(request: Request, user_id: int) -> dict[str, Any]:
        """Alvo de uma acao de governo, ja recusando acao sobre si mesmo.

        A saida de um admin e decisao de outro admin: sem isto, um clique
        errado tranca a instancia com um admin desativado por ele mesmo.
        """
        target = auth_ops.get_user(auth_of(request), user_id)
        if target is None:
            raise _error(404, "user_not_found", "conta inexistente")
        if target["id"] == current_user(request)["id"]:
            raise _error(
                403, "self_demotion",
                "um admin nao altera o proprio papel nem o proprio status",
            )
        return target

    @app.get(API_PREFIX + "/admin/users")
    async def admin_list_users(request: Request):
        return {"users": auth_ops.list_users(auth_of(request))}

    @app.post(API_PREFIX + "/admin/users/{user_id}/approve")
    async def admin_approve(request: Request, user_id: int, payload: ApproveIn):
        target = _target_user(request, user_id)
        conn = auth_of(request)
        # Papel escolhido na propria aprovacao: exigir uma segunda acao so
        # criaria uma janela em que a conta ja entra com o papel errado.
        if payload.role != target["role"]:
            auth_ops.set_role(conn, user_id, payload.role)
        return {"user": auth_ops.set_status(conn, user_id, "active")}

    @app.post(API_PREFIX + "/admin/users/{user_id}/reject")
    async def admin_reject(request: Request, user_id: int):
        _target_user(request, user_id)
        return {"user": auth_ops.set_status(auth_of(request), user_id, "rejected")}

    @app.post(API_PREFIX + "/admin/users/{user_id}/disable")
    async def admin_disable(request: Request, user_id: int):
        _target_user(request, user_id)
        return {"user": auth_ops.set_status(auth_of(request), user_id, "disabled")}

    @app.post(API_PREFIX + "/admin/users/{user_id}/enable")
    async def admin_enable(request: Request, user_id: int):
        _target_user(request, user_id)
        return {"user": auth_ops.set_status(auth_of(request), user_id, "active")}

    @app.put(API_PREFIX + "/admin/users/{user_id}/role")
    async def admin_set_role(request: Request, user_id: int, payload: RoleIn):
        _target_user(request, user_id)
        return {"user": auth_ops.set_role(auth_of(request), user_id, payload.role)}

    @app.post(API_PREFIX + "/admin/users/{user_id}/password")
    async def admin_reset_password(request: Request, user_id: int, payload: ResetIn):
        _target_user(request, user_id)
        conn = auth_of(request)
        # Temporaria por construcao: quem definiu a senha conhece o valor,
        # entao ela so serve para um login.
        auth_ops.set_password(conn, user_id, payload.password, must_change=True)
        return {"user": auth_ops.get_user(conn, user_id)}

    @app.delete(API_PREFIX + "/admin/users/{user_id}/sessions")
    async def admin_revoke_sessions(request: Request, user_id: int):
        target = _target_user(request, user_id)
        # Derrubar quem esta dentro e barrar quem quer entrar sao decisoes
        # separadas: o status da conta nao muda aqui.
        revoked = auth_ops.revoke_user_sessions(auth_of(request), target["id"])
        return {"revoked": revoked,
                "user": auth_ops.get_user(auth_of(request), user_id)}

    @app.get(API_PREFIX + "/admin/activity")
    async def admin_activity(
        request: Request,
        limit: int = 100,
        offset: int = 0,
        user: str = "",
        path: str = "",
        date_from: str = "",
        date_to: str = "",
    ):
        return {"entries": auth_ops.list_activity(
            auth_of(request), limit, offset, user, path, date_from, date_to)}

    @app.get(API_PREFIX + "/admin/access-log")
    async def admin_access_log(request: Request, limit: int = 100, offset: int = 0):
        return {"attempts": auth_ops.list_attempts(auth_of(request), limit, offset)}

    @app.get(API_PREFIX + "/admin/overview")
    async def admin_overview(request: Request):
        conn = conn_of(request)
        ws = ws_of(request)
        meta = {
            row["key"]: row["value"]
            for row in conn.execute("SELECT key, value FROM index_meta")
        }
        trash = ws.arbites_dir / "trash"
        trash_items = (
            len([p for p in trash.iterdir() if not p.name.endswith(".arbtrash")])
            if trash.is_dir() else 0
        )
        return {
            "version": __version__,
            "users": auth_ops.count_users_by_status(auth_of(request)),
            "index": {
                "last_reindex": meta.get("last_reindex"),
                "last_reindex_seconds": meta.get("last_reindex_seconds"),
            },
            "trash_items": trash_items,
            "switches": auth_ops.list_switches(auth_of(request)),
        }

    @app.get(API_PREFIX + "/admin/switches")
    async def get_switches(request: Request):
        # Legivel por qualquer sessao: a UI precisa esconder o que esta
        # desligado, e o estado de um interruptor nao e segredo.
        return {"switches": auth_ops.list_switches(auth_of(request))}

    @app.put(API_PREFIX + "/admin/switches/{name}")
    async def put_switch(request: Request, name: str, payload: SwitchIn):
        user = current_user(request)
        return {"switch": auth_ops.set_switch(
            auth_of(request), name, payload.enabled, user["email"])}

    @app.post(API_PREFIX + "/auth/password")
    async def change_password(request: Request, payload: PasswordIn):
        conn = auth_of(request)
        user = current_user(request)
        row = auth_ops.get_user_by_email(conn, user["email"])
        if not auth_ops.verify_password(row["password_hash"], payload.current_password):
            raise _error(401, "invalid_credentials", "senha atual incorreta")
        auth_ops.set_password(conn, user["id"], payload.new_password)
        # set_password derruba todas as sessoes; quem trocou recebe uma nova
        # (rotacao) para nao ser deslogado pelo proprio acerto.
        token = auth_ops.open_session(
            conn, user["id"], client_ip(request),
            request.headers.get("user-agent", ""),
        )
        response = JSONResponse({"user": auth_ops.get_user(conn, user["id"])})
        _set_session_cookie(response, request, token)
        return response

def _dist_do_frontend() -> str:
    """Onde a SPA é servida. Um lugar só, porque o gate de build (change 0182)
    precisa olhar exatamente a mesma pasta que o mount serve."""
    return os.environ.get(
        "ARBITES_FRONTEND_DIST",
        str(Path(__file__).resolve().parents[2] / "frontend" / "dist"),
    )


def _mount_frontend(app: FastAPI) -> None:
    """Serve o build da SPA (frontend/dist) como estático — um comando sobe tudo."""
    dist = _dist_do_frontend()
    if Path(dist).is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="spa")


app = create_app()
