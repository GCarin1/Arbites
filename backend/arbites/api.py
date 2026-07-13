"""API REST do Arbites — M0.

Base: /api/v1. Erros no formato { "error": { "code", "message" } }.
Toda resposta de escrita retorna a entidade atualizada (contrato http-api).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
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
from pydantic import BaseModel, Field

from . import __version__
from . import audit as audit_ops
from . import context_pack as context_pack_ops
from . import executions as exec_ops
from . import project_memory as memory_ops
from . import risk_map as risk_map_ops
from . import metrics as metrics_ops
from . import ai as ai_ops
from . import daily as daily_ops
from . import xray_import as xray_ops
from .ai import AIKeyStore, AIProviderError
from .ci import CIError, CIManager, HttpxGitHub, TokenStore
from .executions import ExecutionError
from .gherkin_scan import list_feature_files, scan_target
from .runner import RunManager
from .xray_import import XrayImportError
from .indexer import connect, reindex_file, reindex_full
from .parser import parse_markdown
from .watcher import start_watcher
from .workspace import Workspace, slugify

API_PREFIX = "/api/v1"
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
    scenario_tag: str


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


class ExecutionCreate(BaseModel):
    name: str
    sprint: str | None = None
    environment: str | None = None
    squad: str | None = None
    testcase_ids: list[str]
    owner: str = "local"


class ExecutionPatch(BaseModel):
    name: str | None = None
    sprint: str | None = None
    environment: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|in_progress)$")


class ResultStatusIn(BaseModel):
    status: str
    comment: str | None = None
    column: str | None = None
    who: str = "local"


class StepStatusIn(BaseModel):
    status: str
    who: str = "local"


class DefectLinkIn(BaseModel):
    defect_id: str
    who: str = "local"


class LocalRunIn(BaseModel):
    target: str
    tags: list[str] = []
    testcase_ids: list[str] = []
    feature: str | None = None  # .feature específico (behave <arquivo> --tags=)


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


class TokenIn(BaseModel):
    token: str


class AIProviderConfig(BaseModel):
    name: str
    kind: str = "openai_compatible"
    model: str = ""
    base_url: str | None = None


class AIProvidersIn(BaseModel):
    default_provider: str | None = None
    providers: list[AIProviderConfig] = []
    keys: dict[str, str] = {}  # name → chave; vai direto ao keyring


class AutomationTargetIn(BaseModel):
    name: str
    kind: str = "behave"
    local_path: str
    features_glob: str = "features/**/*.feature"
    python_path: str | None = None
    working_dir: str | None = None
    timeout_minutes: float | None = None


class AutomationTargetsIn(BaseModel):
    targets: list[AutomationTargetIn] = []


class GenerateIn(BaseModel):
    source: str  # story_id (ST-XXXX) ou texto/markdown livre
    provider: str | None = None  # default_provider se omitido


class AIByCtIn(BaseModel):
    provider: str | None = None


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


# Catálogo do .env do projeto de automação (doc de ajustes §1.5.1 etapa 5)
ENV_CATALOG: list[dict[str, str]] = [
    {"section": "Credenciais de Teste", "key": "TEST_DOCUMENTO", "description": "Documento (CPF) utilizado para login nos testes"},
    {"section": "Credenciais de Teste", "key": "TEST_SENHA", "description": "Senha do usuário de teste"},
    {"section": "URLs", "key": "BASE_URL", "description": "URL base da aplicação sob teste"},
    {"section": "WebDriver Local", "key": "EDGE_DRIVER_PATH", "description": "Caminho personalizado para o msedgedriver (opcional)"},
    {"section": "WebDriver Local", "key": "HEADLESS", "description": "Executar sem interface gráfica (true/false)"},
    {"section": "WebDriver Manager", "key": "USE_WEBDRIVER_MANAGER", "description": "Se true, baixa o driver automaticamente via webdriver_manager"},
    {"section": "WebDriver Manager", "key": "LOCAL_BROWSER", "description": "Navegador para execução local (edge, chrome)"},
    {"section": "Timeouts", "key": "PAGE_LOAD_TIMEOUT", "description": "Timeout de carregamento de página (segundos)"},
    {"section": "Timeouts", "key": "SCRIPT_TIMEOUT", "description": "Timeout de execução de scripts (segundos)"},
    {"section": "Timeouts", "key": "ELEMENT_WAIT_TIMEOUT", "description": "Timeout de espera por elementos (segundos)"},
    {"section": "BrowserStack — Ativação", "key": "USE_BROWSERSTACK", "description": "Ativar execução remota no BrowserStack (true/false)"},
    {"section": "BrowserStack — Credenciais", "key": "BROWSERSTACK_USERNAME", "description": "Username da conta BrowserStack"},
    {"section": "BrowserStack — Credenciais", "key": "BROWSERSTACK_ACCESS_KEY", "description": "Access Key da conta BrowserStack"},
    {"section": "BrowserStack — Projeto", "key": "BROWSERSTACK_PROJECT_NAME", "description": "Nome do projeto no BrowserStack"},
    {"section": "BrowserStack — Projeto", "key": "BROWSERSTACK_BUILD_NAME", "description": "Nome da build/execução"},
    {"section": "BrowserStack — Browser", "key": "BROWSERSTACK_OS", "description": "Sistema operacional (Windows, OS X)"},
    {"section": "BrowserStack — Browser", "key": "BROWSERSTACK_OS_VERSION", "description": "Versão do SO (11, 10, Ventura, etc.)"},
    {"section": "BrowserStack — Browser", "key": "BROWSERSTACK_BROWSER", "description": "Navegador (Chrome, Firefox, Edge, Safari)"},
    {"section": "BrowserStack — Browser", "key": "BROWSERSTACK_BROWSER_VERSION", "description": "Versão do navegador (latest, 120.0, etc.)"},
    {"section": "BrowserStack — Local Testing", "key": "BROWSERSTACK_LOCAL", "description": "Testar URLs internas/localhost (true/false)"},
    {"section": "Ambiente", "key": "ENVIRONMENT", "description": "Ambiente de execução (dev, staging, prod)"},
    {"section": "Ambiente", "key": "DEBUG", "description": "Habilitar logs de debug (true/false)"},
    {"section": "Logger", "key": "LOG_ENABLED", "description": "Habilitar/desabilitar logs (true/false)"},
    {"section": "Logger", "key": "LOG_LEVEL", "description": "Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)"},
    {"section": "Logger", "key": "LOG_SAVE_TO_FILE", "description": "Salvar logs em arquivo (true/false)"},
    {"section": "Logger", "key": "LOG_SHOW_CONSOLE", "description": "Exibir logs no console (true/false)"},
    {"section": "Logger", "key": "LOG_MAX_FILE_SIZE", "description": "Tamanho máximo do arquivo de log em bytes"},
    {"section": "Logger", "key": "LOG_BACKUP_COUNT", "description": "Quantidade de arquivos de backup de log"},
    {"section": "Análise de Logs com IA", "key": "AI_LOG_ANALYZER_ENABLED", "description": "Habilitar análise de logs com IA (true/false)"},
    {"section": "Análise de Logs com IA", "key": "OPENAI_API_KEY", "description": "Chave de API da OpenAI ou B3GPT"},
    {"section": "Análise de Logs com IA", "key": "OPENAI_BASE_URL", "description": "URL base da API (vazio para OpenAI padrão)"},
    {"section": "Análise de Logs com IA", "key": "OPENAI_API_VERSION", "description": "Versão da API (necessário para B3GPT/Azure)"},
    {"section": "Análise de Logs com IA", "key": "OPENAI_MODEL", "description": "Modelo a ser utilizado (gpt-4o-mini, etc.)"},
    {"section": "Análise de Logs com IA", "key": "OPENAI_MAX_TOKENS", "description": "Máximo de tokens na resposta"},
    {"section": "Análise de Logs com IA", "key": "OPENAI_TEMPERATURE", "description": "Temperatura (0.0 = preciso, 1.0 = criativo)"},
    {"section": "Análise de Logs com IA", "key": "AI_ANALYZE_ON_FAILURE_ONLY", "description": "Analisar apenas em falhas (true/false)"},
    {"section": "Análise de Logs com IA", "key": "AI_SAVE_ANALYSIS_TO_FILE", "description": "Salvar análises em arquivo (true/false)"},
    {"section": "Análise de Logs com IA", "key": "AI_MAX_LOG_LINES", "description": "Máximo de linhas do log enviadas para análise"},
]

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
) -> FastAPI:
    ws = Workspace(workspace_root or os.environ.get("ARBITES_WORKSPACE", "workspace"))
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
        app.state.ci = CIManager(ws, app.state.conn, github, tokens)
        app.state.ai_keys = ai_keys
        app.state.ai_transport = ai_transport
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

    @app.exception_handler(CIError)
    async def _ci_error(request: Request, exc: CIError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(AIProviderError)
    async def _ai_error(request: Request, exc: AIProviderError):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

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
    _, out["body"] = _load_doc(ws, row["path"])
    return out


def _tc_out(conn: sqlite3.Connection, ws: Workspace, entity_id: str) -> dict:
    row = conn.execute("SELECT * FROM testcases WHERE id = ?", (entity_id,)).fetchone()
    if not row:
        raise _error(404, "not_found", f"{entity_id} não encontrado")
    out = dict(row)
    out["tags"] = [
        r["tag"]
        for r in conn.execute(
            "SELECT tag FROM tc_tags WHERE testcase_id = ?", (entity_id,)
        )
    ]
    _, out["body"] = _load_doc(ws, row["path"])
    return out


# ---------------------------------------------------------------------------
# Rotas


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

    @app.get(API_PREFIX + "/warnings")
    async def get_warnings(request: Request):
        return [
            dict(row)
            for row in conn_of(request).execute(
                "SELECT source_path, code, message, created_at FROM warnings"
                " ORDER BY source_path, code"
            )
        ]

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

    @app.put(API_PREFIX + "/requirements/{entity_id}")
    async def update_requirement(request: Request, entity_id: str, payload: RequirementUpdate):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "requirements", entity_id)
        meta, body = _load_doc(ws, rel)
        changes = payload.model_dump(exclude_unset=True)
        body = changes.pop("body", body)
        if "squad" in changes and not changes["squad"]:
            meta.pop("squad", None)
            changes.pop("squad")
        meta.update(changes)
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        return _req_out(conn, ws, entity_id)

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
        folder: str = "",
        squad: str = "",
        q: str = "",
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
            ("squad_effective", squad),
        ):
            if value:
                sql += f" AND t.{field} = ?"
                params.append(value)
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
        }
        if payload.squad:
            meta["squad"] = payload.squad
        if payload.automation is not None:
            meta["automation"] = payload.automation.model_dump()
        folder = payload.folder.strip("/").replace("\\", "/")
        target_dir = ws.root / "testcases" / folder if folder else ws.root / "testcases"
        if not str(target_dir.resolve()).startswith(str((ws.root / "testcases").resolve())):
            raise _error(422, "invalid_folder", "folder fora de testcases/")
        path = target_dir / f"{new_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body if payload.body is not None else DEFAULT_TC_BODY)
        reindex_file(ws, conn, path)
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
        for new_md in dest.rglob("*.md"):
            reindex_file(ws, conn, new_md)  # indexa no caminho novo
        return {"path": ws.relpath(dest)}

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
        if "squad" in changes and not changes["squad"]:
            meta.pop("squad", None)
            changes.pop("squad")
        meta.update(changes)
        meta["updated"] = date.today().isoformat()
        _write_doc(ws.root / rel, meta, body)
        reindex_file(ws, conn, ws.root / rel)
        return _tc_out(conn, ws, entity_id)

    @app.delete(API_PREFIX + "/testcases/{entity_id}", status_code=204)
    async def delete_testcase(request: Request, entity_id: str):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "testcases", entity_id)
        path = ws.root / rel
        ws.trash(path)
        reindex_file(ws, conn, path)

    @app.get(API_PREFIX + "/testcases/{entity_id}/raw", response_class=PlainTextResponse)
    async def get_testcase_raw(request: Request, entity_id: str):
        ws = ws_of(request)
        rel = _find_path(conn_of(request), "testcases", entity_id)
        return (ws.root / rel).read_text(encoding="utf-8")

    @app.put(API_PREFIX + "/testcases/{entity_id}/raw")
    async def put_testcase_raw(request: Request, entity_id: str, payload: RawIn):
        ws, conn = ws_of(request), conn_of(request)
        rel = _find_path(conn, "testcases", entity_id)
        (ws.root / rel).write_text(payload.content, encoding="utf-8")
        reindex_file(ws, conn, ws.root / rel)
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
            ws, payload.name, payload.owner, payload.sprint, payload.environment,
            testcases, squad=payload.squad,
        )
        _save_and_index(ws, conn, execution)
        return execution

    @app.get(API_PREFIX + "/executions/{exec_id}")
    async def get_execution(request: Request, exec_id: str):
        return exec_ops.load(ws_of(request), exec_id)

    @app.patch(API_PREFIX + "/executions/{exec_id}")
    async def patch_execution(request: Request, exec_id: str, payload: ExecutionPatch):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        if execution["status"] == "closed":
            raise _error(409, "execution_closed", f"{exec_id} está fechada")
        for key, value in payload.model_dump(exclude_unset=True).items():
            execution[key] = value
        _save_and_index(ws, conn, execution)
        return execution

    @app.post(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/status")
    async def post_result_status(
        request: Request, exec_id: str, ct_id: str, payload: ResultStatusIn
    ):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.set_result_status(
            execution, ct_id, payload.status, payload.who, payload.comment, payload.column
        )
        _save_and_index(ws, conn, execution)
        return execution

    @app.post(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/steps/{step_index}")
    async def post_step_status(
        request: Request, exec_id: str, ct_id: str, step_index: int, payload: StepStatusIn
    ):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.set_step_status(execution, ct_id, step_index, payload.status, payload.who)
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
        who: str = Form(default="local"),
    ):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        content = await file.read()
        evidence = exec_ops.add_evidence(
            ws,
            execution,
            ct_id,
            file.filename or "evidencia.bin",
            content,
            file.content_type,
            note,
            who,
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
        exec_ops.link_defect(execution, ct_id, payload.defect_id, payload.who)
        _save_and_index(ws, conn, execution)
        return execution

    @app.delete(API_PREFIX + "/executions/{exec_id}/results/{ct_id}/defects/{defect_id}")
    async def delete_link_defect(request: Request, exec_id: str, ct_id: str, defect_id: str):
        ws, conn = ws_of(request), conn_of(request)
        execution = exec_ops.load(ws, exec_id)
        exec_ops.unlink_defect(execution, ct_id, defect_id, "local")
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
        return metrics_ops.annotate_thresholds(summary, thresholds)

    @app.get(API_PREFIX + "/metrics/trend")
    async def metrics_trend(request: Request, days: int = 7, sprint: str = "", squad: str = ""):
        if days not in (7, 15, 30):
            raise _error(422, "invalid_days", "days deve ser 7, 15 ou 30")
        return metrics_ops.trend(conn_of(request), days, sprint or None, squad or None)

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
        request: Request, format: str = "md", epic: str = "", sprint: str = "", squad: str = ""
    ):
        matrix = metrics_ops.traceability(
            conn_of(request), epic or None, sprint or None, squad or None
        )
        if format == "md":
            return PlainTextResponse(
                metrics_ops.matrix_markdown(matrix),
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="matriz.md"'},
            )
        if format == "pdf":
            from .export_pdf import matrix_pdf

            return Response(
                content=matrix_pdf(matrix),
                media_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="matriz.pdf"'},
            )
        raise _error(422, "invalid_format", "format deve ser md ou pdf")

    @app.get(API_PREFIX + "/context-pack")
    async def get_context_pack(
        request: Request, epic: str = "", story: str = "", squad: str = ""
    ):
        if not (epic or story or squad):
            raise _error(
                422, "scope_required",
                "informe epic, story ou squad — o context pack não exporta o"
                " workspace inteiro sem escopo",
            )
        ws, conn = ws_of(request), conn_of(request)
        body = context_pack_ops.build(
            conn, ws.root, epic or None, story or None, squad or None
        )
        return PlainTextResponse(
            body,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="context-pack.md"'},
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
        ws, conn = ws_of(request), conn_of(request)
        runner: RunManager = request.app.state.runner
        import yaml as _yaml

        config = ws.config()
        config["automation_targets"] = [
            t.model_dump(exclude_none=True) for t in payload.targets
        ]
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
        features_glob: str = "features/**/*.feature",
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

    @app.post(API_PREFIX + "/targets/{name}/scan")
    async def scan_target_route(request: Request, name: str):
        ws, conn = ws_of(request), conn_of(request)
        return scan_target(ws, conn, _find_target(ws, name))

    @app.get(API_PREFIX + "/targets/{name}/features")
    async def target_features(request: Request, name: str):
        """Arquivos .feature e tags do target (para os dropdowns do run)."""
        conn = conn_of(request)
        rows = conn.execute(
            "SELECT feature_path, tag, scenario_name FROM scenarios WHERE target = ?"
            " ORDER BY feature_path, line",
            (name,),
        ).fetchall()
        features: dict[str, int] = {}
        tags: set[str] = set()
        for r in rows:
            features[r["feature_path"]] = features.get(r["feature_path"], 0) + 1
            tags.add(r["tag"])
        return {
            "features": [
                {"path": p, "scenarios": n} for p, n in sorted(features.items())
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
    async def env_catalog(request: Request):
        return {"catalog": ENV_CATALOG}

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

        # resolve seleção → CTs da execution + tags do behave
        ct_ids: list[str] = list(payload.testcase_ids)
        tags: list[str] = [t if t.startswith("@") else f"@{t}" for t in payload.tags]
        if payload.feature and not ct_ids and not tags:
            # rodar um .feature inteiro: CTs = cenários daquele arquivo
            rows = conn.execute(
                "SELECT tag FROM scenarios WHERE target = ? AND feature_path = ?",
                (payload.target, payload.feature),
            ).fetchall()
            ct_ids = sorted({r["tag"].lstrip("@") for r in rows})
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
        if not ct_ids:
            raise _error(422, "empty_selection",
                         "informe testcase_ids, tags ou feature que resolvam para CTs")
        if not tags and not payload.feature:
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

        execution = runner.submit(target, testcases, tags, feature=payload.feature)
        return {
            "execution": execution,
            "run": runner.runs[execution["id"]].snapshot(),
        }

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
                        line = await queue.get()
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

    @app.get(API_PREFIX + "/settings/github/token")
    async def github_token_status(request: Request):
        return request.app.state.tokens.status()  # status apenas, nunca o valor

    @app.put(API_PREFIX + "/settings/github/token")
    async def github_token_set(request: Request, payload: TokenIn):
        request.app.state.tokens.set(payload.token)
        return request.app.state.tokens.status()

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

    def _profile_path(ws: Workspace) -> Path:
        return ws.root / "profile.md"

    def _load_profile(ws: Workspace) -> tuple[str, str]:
        path = _profile_path(ws)
        if not path.exists():
            _write_doc(path, {"name": ""}, PROFILE_TEMPLATE)
        meta, body = _load_doc(ws, ws.relpath(path))
        return str(meta.get("name") or ""), body

    @app.get(API_PREFIX + "/profile")
    async def get_profile(request: Request):
        name, memory = _load_profile(ws_of(request))
        return {"name": name, "memory": memory}

    @app.put(API_PREFIX + "/profile")
    async def put_profile(request: Request, payload: ProfileIn):
        ws = ws_of(request)
        name, memory = _load_profile(ws)
        if payload.name is not None:
            name = payload.name
        if payload.memory is not None:
            memory = payload.memory
        _write_doc(_profile_path(ws), {"name": name or None}, memory)
        return {"name": name, "memory": memory}

    def _with_memory(ws: Workspace, user_text: str) -> str:
        """Prefixa o conteúdo do usuário com a memória de longo prazo (doc §2).

        Injetado em TODA chamada de IA, independente do provider. Memória
        vazia/template intocado → sem bloco (prompt limpo).
        """
        try:
            _, memory = _load_profile(ws)
        except OSError:
            return user_text
        stripped = memory.strip()
        if not stripped or stripped == PROFILE_TEMPLATE.strip():
            return user_text
        return (
            "Contexto persistente do usuário (memória de longo prazo):\n"
            f"{stripped}\n\n---\n\n{user_text}"
        )

    def _with_project_recap(conn: sqlite3.Connection, ws: Workspace, user_text: str) -> str:
        """Empilha o recap de decisões/lições recentes (Memória Histórica do
        Projeto) sobre a memória de longo prazo do usuário — a IA "lembra"
        do que já aconteceu no projeto, não só do que o usuário escreveu no
        perfil."""
        recap = memory_ops.recent_recap(conn)
        text = f"{recap}\n\n---\n\n{user_text}" if recap else user_text
        return _with_memory(ws, text)

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
        generated = await asyncio.to_thread(
            ai_ops.generate_testcases, provider, _with_project_recap(conn, ws, source), lessons
        )
        lessons_used = [{"id": l["id"], "title": l["title"]} for l in lessons]
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
            ai_ops.review_testcase, provider, _with_project_recap(conn, ws, ct_md), similar
        )
        _log_agent_event(
            ws, conn, "review_testcase", ct_id, row["title"] if row else None,
            f"Revisou {ct_id}: {len(result.issues)} issue(s) encontrado(s)",
        )
        return {"preview": True, "similar_considered": similar,
                **result.model_dump()}

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
            ai_ops.negative_cases, provider, _with_memory(ws, ct_md)
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
            ai_ops.convert_import, prov, name, _with_memory(ws, text)
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
    async def list_defects(request: Request, status: str = "", has_lesson: bool = False):
        sql, params = "SELECT * FROM defects WHERE 1=1", []
        if status:
            sql += " AND status = ?"
            params.append(status)
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
            "root_cause": payload.root_cause,
            "fix": payload.fix,
            "prevention": payload.prevention,
        }
        path = ws.root / "defects" / f"{defect_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body)
        reindex_file(ws, conn, path)
        if payload.execution and payload.testcase:
            execution = exec_ops.load(ws, payload.execution)
            exec_ops.link_defect(execution, payload.testcase, defect_id, "local")
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

    def _todo_out(conn, ws: Workspace, todo_id: str) -> dict:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if not row:
            raise _error(404, "not_found", f"{todo_id} não encontrado")
        out = dict(row)
        link_ids = [x for x in (row["links"] or "").split(",") if x]
        out["links"] = [_resolve_link(conn, x) for x in link_ids]
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
            out.append(item)
        return out

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
            ai_ops.generate_daily, provider, _with_memory(ws, markdown)
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
            ai_ops.summarize_meeting, provider, _with_memory(ws, body)
        )
        return {"preview": True, "id": meeting_id, **result.model_dump()}

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

    @app.get(API_PREFIX + "/audit/{audit_id}")
    async def get_audit(request: Request, audit_id: str):
        return _audit_out(conn_of(request), ws_of(request), audit_id)

    # -- memory / Memória Histórica do Projeto --------------------------
    # Linha do tempo cronológica (estilo git log) cruzando requisitos,
    # defeitos, lições aprendidas, decisões arquiteturais e interações de
    # agentes de IA — nada persistido além de `agent_events` (ver
    # `_log_agent_event`); o resto é derivado do que já está no índice.

    @app.get(API_PREFIX + "/memory/timeline")
    async def get_memory_timeline(request: Request, kinds: str = "", limit: int = 50):
        wanted = [k for k in kinds.split(",") if k] or None
        return memory_ops.timeline(conn_of(request), wanted, max(1, min(limit, 200)))


def _mount_frontend(app: FastAPI) -> None:
    """Serve o build da SPA (frontend/dist) como estático — um comando sobe tudo."""
    dist = os.environ.get(
        "ARBITES_FRONTEND_DIST",
        str(Path(__file__).resolve().parents[2] / "frontend" / "dist"),
    )
    if Path(dist).is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="spa")


app = create_app()
