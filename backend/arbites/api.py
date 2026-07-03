"""API REST do Arbites — M0.

Base: /api/v1. Erros no formato { "error": { "code", "message" } }.
Toda resposta de escrita retorna a entidade atualizada (contrato http-api).
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .indexer import connect, reindex_file, reindex_full
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
) -> FastAPI:
    ws = Workspace(workspace_root or os.environ.get("ARBITES_WORKSPACE", "workspace"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ws.ensure()
        app.state.ws = ws
        app.state.conn = connect(ws)
        app.state.conn.execute("PRAGMA busy_timeout=5000")
        reindex_full(ws, app.state.conn)
        observer = None
        if watch:
            watch_conn = connect(ws)
            watch_conn.execute("PRAGMA busy_timeout=5000")
            observer = start_watcher(ws, watch_conn)
        yield
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


def _mount_frontend(app: FastAPI) -> None:
    """Serve o build da SPA (frontend/dist) como estático — um comando sobe tudo."""
    dist = os.environ.get(
        "ARBITES_FRONTEND_DIST",
        str(Path(__file__).resolve().parents[2] / "frontend" / "dist"),
    )
    if Path(dist).is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="spa")


app = create_app()
