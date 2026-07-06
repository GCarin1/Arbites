"""API REST do Arbites — M0.

Base: /api/v1. Erros no formato { "error": { "code", "message" } }.
Toda resposta de escrita retorna a entidade atualizada (contrato http-api).
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

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
from . import executions as exec_ops
from . import metrics as metrics_ops
from . import ai as ai_ops
from . import xray_import as xray_ops
from .ai import AIKeyStore, AIProviderError
from .ci import CIError, CIManager, HttpxGitHub, TokenStore
from .executions import ExecutionError
from .gherkin_scan import scan_target
from .runner import RunManager
from .xray_import import XrayImportError
from .indexer import connect, reindex_file, reindex_full
from .parser import parse_markdown
from .watcher import start_watcher
from .workspace import Workspace, slugify

API_PREFIX = "/api/v1"


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
    body: str = ""


class RequirementUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    epic: str | None = None
    external_key: str | None = None
    confluence_url: str | None = None
    tags: list[str] | None = None
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
    automation: AutomationRef | None = None
    body: str | None = None


class RawIn(BaseModel):
    content: str


class ExecutionCreate(BaseModel):
    name: str
    sprint: str | None = None
    environment: str | None = None
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


class LocalRunIn(BaseModel):
    target: str
    tags: list[str] = []
    testcase_ids: list[str] = []


class CIRunIn(BaseModel):
    target: str
    ref: str | None = None
    tags: list[str] = []
    testcase_ids: list[str] = []


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


class DefectUpdate(BaseModel):
    title: str | None = None
    severity: str | None = None
    status: str | None = None
    testcase: str | None = None
    execution: str | None = None
    external_key: str | None = None
    body: str | None = None


DEFAULT_TC_BODY = """## Objetivo

## Pré-condições

-

## Passos

1.

## Resultado esperado

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
            for row in conn.execute("SELECT id, title, type, status, path FROM testcases")
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
                        }
                    )
            return node

        root = walk(ws.root / "testcases")
        root["name"] = "testcases"
        return root

    # -- requirements ----------------------------------------------------

    @app.get(API_PREFIX + "/requirements")
    async def list_requirements(request: Request, kind: str = "", status: str = ""):
        sql, params = "SELECT * FROM requirements WHERE 1=1", []
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if status:
            sql += " AND status = ?"
            params.append(status)
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
        }
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
        q: str = "",
    ):
        sql, params = "SELECT DISTINCT t.* FROM testcases t", []
        if tag:
            sql += " JOIN tc_tags g ON g.testcase_id = t.id AND g.tag = ?"
            params.append(tag)
        sql += " WHERE 1=1"
        for field, value in (("story_id", story), ("status", status), ("type", type)):
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

    # -- executions (M1) ---------------------------------------------------

    def _save_and_index(ws: Workspace, conn, execution: dict) -> None:
        path = exec_ops.save(ws, execution)
        reindex_file(ws, conn, path)

    @app.get(API_PREFIX + "/executions")
    async def list_executions(
        request: Request, sprint: str = "", status: str = "", origin: str = ""
    ):
        conn = conn_of(request)
        sql, params = "SELECT * FROM executions WHERE 1=1", []
        for field, value in (("sprint", sprint), ("status", status), ("origin", origin)):
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
            ws, payload.name, payload.owner, payload.sprint, payload.environment, testcases
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
        request: Request, sprint: str = "", days: int = 0, epic: str = ""
    ):
        conn = conn_of(request)
        s, d = sprint or None, days or None
        return {
            "requirement_coverage": metrics_ops.requirement_coverage(conn, epic or None),
            "execution_coverage": metrics_ops.execution_coverage(conn, s, d),
            "pass_rate": metrics_ops.pass_rate(conn, s, d),
            "blocked_rate": metrics_ops.blocked_rate(conn, s, d),
            "rework_rate": metrics_ops.rework_rate(conn, s, d),
        }

    @app.get(API_PREFIX + "/metrics/trend")
    async def metrics_trend(request: Request, days: int = 7, sprint: str = ""):
        if days not in (7, 15, 30):
            raise _error(422, "invalid_days", "days deve ser 7, 15 ou 30")
        return metrics_ops.trend(conn_of(request), days, sprint or None)

    @app.get(API_PREFIX + "/metrics/coverage")
    async def metrics_coverage(request: Request, epic: str = ""):
        return metrics_ops.requirement_coverage(conn_of(request), epic or None)

    @app.get(API_PREFIX + "/metrics/flaky")
    async def metrics_flaky(request: Request, window: int = 5):
        return metrics_ops.flaky(conn_of(request), window)

    @app.get(API_PREFIX + "/metrics/traceability")
    async def metrics_traceability(request: Request, epic: str = "", sprint: str = ""):
        return metrics_ops.traceability(conn_of(request), epic or None, sprint or None)

    @app.get(API_PREFIX + "/metrics/traceability/export")
    async def metrics_traceability_export(
        request: Request, format: str = "md", epic: str = "", sprint: str = ""
    ):
        matrix = metrics_ops.traceability(conn_of(request), epic or None, sprint or None)
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

    @app.get(API_PREFIX + "/targets")
    async def list_targets(request: Request):
        ws, conn = ws_of(request), conn_of(request)
        runner: RunManager = request.app.state.runner
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
                    "scenarios": scenarios,
                    "queue_length": runner.queue_length(str(name)),
                }
            )
        return out

    @app.post(API_PREFIX + "/targets/{name}/scan")
    async def scan_target_route(request: Request, name: str):
        ws, conn = ws_of(request), conn_of(request)
        return scan_target(ws, conn, _find_target(ws, name))

    @app.post(API_PREFIX + "/runs/local", status_code=201)
    async def create_local_run(request: Request, payload: LocalRunIn):
        ws, conn = ws_of(request), conn_of(request)
        runner: RunManager = request.app.state.runner
        target = _find_target(ws, payload.target)

        # resolve seleção → CTs da execution + tags do behave
        ct_ids: list[str] = list(payload.testcase_ids)
        tags: list[str] = [t if t.startswith("@") else f"@{t}" for t in payload.tags]
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
                         "informe testcase_ids ou tags que resolvam para CTs")
        if not tags:
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
                raise _error(404, "not_found", f"{ct_id} não encontrado")
            doc = parse_markdown(ws.root / row["path"])
            testcases.append({"id": ct_id, "steps": doc.steps})

        execution = runner.submit(target, testcases, tags)
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

    def _preview_out(generated: ai_ops.GeneratedTestcases) -> dict:
        return {
            "preview": True,  # nada foi gravado; aceite = POST /testcases
            "testcases": [
                {**item.model_dump(), "body": ai_ops.testcase_body(item)}
                for item in generated.testcases
            ],
        }

    @app.post(API_PREFIX + "/ai/generate-testcases")
    async def ai_generate(request: Request, payload: GenerateIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        source = payload.source.strip()
        if source.upper().startswith(("ST-", "EP-")) and len(source) < 32:
            rel = _find_path(conn, "requirements", source.upper())
            source = (ws.root / rel).read_text(encoding="utf-8-sig")
        generated = await asyncio.to_thread(
            ai_ops.generate_testcases, provider, source
        )
        return _preview_out(generated)

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
            ai_ops.review_testcase, provider, ct_md, similar
        )
        return {"preview": True, "similar_considered": similar,
                **result.model_dump()}

    @app.post(API_PREFIX + "/ai/negative-cases/{ct_id}")
    async def ai_negative(request: Request, ct_id: str, payload: AIByCtIn):
        ws, conn = ws_of(request), conn_of(request)
        provider = _ai_provider(request, payload.provider)
        rel = _find_path(conn, "testcases", ct_id)
        ct_md = (ws.root / rel).read_text(encoding="utf-8-sig")
        generated = await asyncio.to_thread(ai_ops.negative_cases, provider, ct_md)
        return _preview_out(generated)

    # -- defects (M1, mínimo) ---------------------------------------------

    def _defect_out(conn, ws: Workspace, defect_id: str) -> dict:
        row = conn.execute("SELECT * FROM defects WHERE id = ?", (defect_id,)).fetchone()
        if not row:
            raise _error(404, "not_found", f"{defect_id} não encontrado")
        out = dict(row)
        _, out["body"] = _load_doc(ws, row["path"])
        return out

    @app.get(API_PREFIX + "/defects")
    async def list_defects(request: Request, status: str = ""):
        sql, params = "SELECT * FROM defects WHERE 1=1", []
        if status:
            sql += " AND status = ?"
            params.append(status)
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
        }
        path = ws.root / "defects" / f"{defect_id}-{slugify(payload.title)}.md"
        _write_doc(path, meta, payload.body)
        reindex_file(ws, conn, path)
        if payload.execution and payload.testcase:
            execution = exec_ops.load(ws, payload.execution)
            exec_ops.link_defect(execution, payload.testcase, defect_id, "local")
            _save_and_index(ws, conn, execution)
        return _defect_out(conn, ws, defect_id)

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


def _mount_frontend(app: FastAPI) -> None:
    """Serve o build da SPA (frontend/dist) como estático — um comando sobe tudo."""
    dist = os.environ.get(
        "ARBITES_FRONTEND_DIST",
        str(Path(__file__).resolve().parents[2] / "frontend" / "dist"),
    )
    if Path(dist).is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="spa")


app = create_app()
