"""Indexer — SQLite descartável reconstruído do filesystem (ADR 0001).

`reindex_full` varre o workspace inteiro; `reindex_file` reparseia um único
arquivo (usado pelo watcher). Apagar o banco nunca perde dados.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .parser import ParsedDoc, check_testcase_headings, parse_markdown, parse_text
from .workspace import Workspace

SCHEMA = """
CREATE TABLE IF NOT EXISTS requirements(
  id TEXT PRIMARY KEY, kind TEXT, title TEXT, epic_id TEXT, status TEXT,
  external_key TEXT, confluence_url TEXT, tags TEXT, path TEXT, mtime REAL,
  squad TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS testcases(
  id TEXT PRIMARY KEY, title TEXT, type TEXT, priority TEXT, status TEXT,
  story_id TEXT, path TEXT, mtime REAL,
  automation_target TEXT, scenario_tag TEXT, external_key TEXT,
  squad TEXT, squad_effective TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS tc_tags(testcase_id TEXT, tag TEXT);
CREATE TABLE IF NOT EXISTS scenarios(
  target TEXT, tag TEXT PRIMARY KEY, feature_path TEXT,
  scenario_name TEXT, line INTEGER, language TEXT);
CREATE TABLE IF NOT EXISTS executions(
  id TEXT PRIMARY KEY, name TEXT, owner TEXT, sprint TEXT, environment TEXT,
  origin TEXT, status TEXT, created_at TEXT, closed_at TEXT, path TEXT,
  squad TEXT);
CREATE TABLE IF NOT EXISTS results(
  execution_id TEXT, testcase_id TEXT, status TEXT, executed_at TEXT,
  duration_seconds REAL, PRIMARY KEY(execution_id, testcase_id));
CREATE TABLE IF NOT EXISTS result_events(
  execution_id TEXT, testcase_id TEXT, status TEXT, at TEXT);
CREATE TABLE IF NOT EXISTS evidences(
  execution_id TEXT, testcase_id TEXT, path TEXT, sha256 TEXT,
  mime TEXT, captured_at TEXT);
CREATE TABLE IF NOT EXISTS defects(
  id TEXT PRIMARY KEY, title TEXT, status TEXT, severity TEXT,
  testcase_id TEXT, execution_id TEXT, external_key TEXT, path TEXT,
  opened_at TEXT);
CREATE TABLE IF NOT EXISTS todos(
  id TEXT PRIMARY KEY, title TEXT, status TEXT, due TEXT, squad TEXT,
  links TEXT, created TEXT, path TEXT, mtime REAL);
CREATE TABLE IF NOT EXISTS meetings(
  id TEXT PRIMARY KEY, title TEXT, date TEXT, summary TEXT, path TEXT, mtime REAL);
CREATE TABLE IF NOT EXISTS warnings(
  source_path TEXT, code TEXT, message TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS index_meta(key TEXT PRIMARY KEY, value TEXT);
"""

_ID_RE = re.compile(r"^([A-Z]+)-(\d+)$")


def connect(ws: Workspace) -> sqlite3.Connection:
    ws.arbites_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ws.index_db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # migração tolerante para índices criados antes da coluna (descartável)
    for ddl in (
        "ALTER TABLE testcases ADD COLUMN external_key TEXT",
        "ALTER TABLE testcases ADD COLUMN squad TEXT",
        "ALTER TABLE testcases ADD COLUMN squad_effective TEXT",
        "ALTER TABLE requirements ADD COLUMN squad TEXT",
        "ALTER TABLE executions ADD COLUMN squad TEXT",
        "ALTER TABLE defects ADD COLUMN opened_at TEXT",
        "ALTER TABLE testcases ADD COLUMN created TEXT",
        "ALTER TABLE requirements ADD COLUMN created TEXT",
    ):
        try:
            conn.execute(ddl)
        except sqlite3.OperationalError:
            pass
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _add_warning(conn: sqlite3.Connection, path: str, code: str, message: str) -> None:
    conn.execute(
        "INSERT INTO warnings(source_path, code, message, created_at) VALUES (?,?,?,?)",
        (path, code, message, _now()),
    )


def _tags(doc: ParsedDoc) -> list[str]:
    raw = doc.meta.get("tags") or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(t) for t in raw]


def reindex_full(ws: Workspace, conn: sqlite3.Connection) -> dict:
    """Varre o workspace inteiro e reconstrói o índice. Meta: < 5 s p/ 2.000 CTs."""
    started = time.perf_counter()
    conn.execute("DELETE FROM requirements")
    conn.execute("DELETE FROM testcases")
    conn.execute("DELETE FROM tc_tags")
    conn.execute("DELETE FROM defects")
    conn.execute("DELETE FROM executions")
    conn.execute("DELETE FROM results")
    conn.execute("DELETE FROM result_events")
    conn.execute("DELETE FROM evidences")
    conn.execute("DELETE FROM todos")
    conn.execute("DELETE FROM meetings")
    conn.execute("DELETE FROM warnings")

    seen_ids: dict[str, str] = {}  # id -> relpath (detecção de duplicidade)
    max_by_prefix: dict[str, int] = {}

    def track_id(doc: ParsedDoc, rel: str) -> bool:
        """Registra o ID; retorna False (conflito) se duplicado."""
        if doc.id is None:
            return False
        m = _ID_RE.match(doc.id)
        if m:
            prefix, num = m.group(1), int(m.group(2))
            max_by_prefix[prefix] = max(max_by_prefix.get(prefix, 0), num)
        if doc.id in seen_ids:
            for p in (seen_ids[doc.id], rel):
                _add_warning(
                    conn, p, "duplicate_id",
                    f"ID {doc.id} duplicado em {seen_ids[doc.id]} e {rel} — conflito",
                )
            return False
        seen_ids[doc.id] = rel
        return True

    # leitura em paralelo: no Windows o open() por arquivo custa ms (AV);
    # I/O solta o GIL, então threads cortam o tempo total por ~n workers
    def read_all(directory: Path) -> list[tuple[Path, str | None, str | None]]:
        paths = sorted(directory.rglob("*.md"))

        def read_one(p: Path) -> tuple[Path, str | None, str | None]:
            try:
                return p, p.read_text(encoding="utf-8-sig"), None
            except OSError as exc:
                return p, None, str(exc)

        if not paths:
            return []
        with ThreadPoolExecutor(max_workers=min(32, 4 * (os.cpu_count() or 4))) as pool:
            return list(pool.map(read_one, paths))

    def parse_one(path: Path, text: str | None, error: str | None) -> ParsedDoc:
        if text is None:
            doc = ParsedDoc(path=path)
            doc.warnings.append(("unreadable", f"{path.name}: {error}"))
            return doc
        return parse_text(path, text)

    for path, text, error in read_all(ws.root / "requirements"):
        doc = parse_one(path, text, error)
        rel = ws.relpath(path)
        _flush_doc_warnings(conn, doc, rel)
        if doc.id and track_id(doc, rel):
            _insert_requirement(conn, doc, rel)

    for path, text, error in read_all(ws.root / "testcases"):
        doc = parse_one(path, text, error)
        check_testcase_headings(doc)
        rel = ws.relpath(path)
        _flush_doc_warnings(conn, doc, rel)
        if doc.id and track_id(doc, rel):
            _insert_testcase(conn, doc, rel)

    for path, text, error in read_all(ws.root / "defects"):
        doc = parse_one(path, text, error)
        rel = ws.relpath(path)
        _flush_doc_warnings(conn, doc, rel)
        if doc.id and track_id(doc, rel):
            _insert_defect(conn, doc, rel)

    for path, text, error in read_all(ws.root / "todos"):
        doc = parse_one(path, text, error)
        rel = ws.relpath(path)
        _flush_doc_warnings(conn, doc, rel)
        if doc.id and track_id(doc, rel):
            _insert_todo(conn, doc, rel)

    for path, text, error in read_all(ws.root / "meetings"):
        doc = parse_one(path, text, error)
        rel = ws.relpath(path)
        _flush_doc_warnings(conn, doc, rel)
        if doc.id and track_id(doc, rel):
            _insert_meeting(conn, doc, rel)

    exec_base = ws.root / "executions"
    if exec_base.exists():
        for path in sorted(exec_base.glob("*/*/execution.json")):
            rel = ws.relpath(path)
            _index_execution(conn, ws, path, rel, max_by_prefix)

    _recompute_effective_squads(conn)
    _relational_checks(conn)

    # scan dos feature files dos automation targets (spec indexing / ADR 0003)
    from .gherkin_scan import scan_all_targets

    scan_all_targets(ws, conn)

    for prefix, seen_max in max_by_prefix.items():
        ws.bump_counter_to(prefix, seen_max)

    duration = time.perf_counter() - started
    conn.execute(
        "INSERT OR REPLACE INTO index_meta(key, value) VALUES ('last_reindex', ?)",
        (_now(),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO index_meta(key, value) VALUES ('last_reindex_seconds', ?)",
        (f"{duration:.3f}",),
    )
    conn.commit()
    return {
        "duration_seconds": round(duration, 3),
        "requirements": conn.execute("SELECT COUNT(*) c FROM requirements").fetchone()["c"],
        "testcases": conn.execute("SELECT COUNT(*) c FROM testcases").fetchone()["c"],
        "defects": conn.execute("SELECT COUNT(*) c FROM defects").fetchone()["c"],
        "warnings": conn.execute("SELECT COUNT(*) c FROM warnings").fetchone()["c"],
    }


def reindex_file(ws: Workspace, conn: sqlite3.Connection, path: Path) -> None:
    """Incremental: reparseia um único arquivo (edição externa → UI em segundos).

    O watcher (thread própria, conexão própria) e os handlers HTTP (outra
    conexão) podem chamar isto quase ao mesmo tempo — uma operação em lote
    (ex.: mover uma pasta com vários CTs) dispara uma rajada de eventos do
    watcher que colide com o loop de reindex do próprio handler. `busy_timeout`
    (PRAGMA, 5s) cobre a maioria dos casos, mas não todos — por isso retenta
    aqui, com rollback entre tentativas para não deixar a transação num
    estado parcial.
    """
    for attempt in range(5):
        try:
            _reindex_file_once(ws, conn, path)
            return
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            conn.rollback()
            if attempt == 4:
                raise
            time.sleep(0.05 * (attempt + 1))


def _reindex_file_once(ws: Workspace, conn: sqlite3.Connection, path: Path) -> None:
    rel = ws.relpath(path)
    if rel.split("/", 1)[0] == "executions" and path.name == "execution.json":
        _drop_execution_rows(conn, rel)
        conn.execute("DELETE FROM warnings WHERE source_path = ?", (rel,))
        if path.exists():
            _index_execution(conn, ws, path, rel, {})
        conn.commit()
        return
    conn.execute("DELETE FROM warnings WHERE source_path = ?", (rel,))
    for table in ("requirements", "testcases", "defects", "todos", "meetings"):
        for row in conn.execute(f"SELECT id FROM {table} WHERE path = ?", (rel,)):
            if table == "testcases":
                conn.execute("DELETE FROM tc_tags WHERE testcase_id = ?", (row["id"],))
        conn.execute(f"DELETE FROM {table} WHERE path = ?", (rel,))

    if path.exists():
        doc = parse_markdown(path)
        top = rel.split("/", 1)[0]
        if top == "testcases":
            check_testcase_headings(doc)
        _flush_doc_warnings(conn, doc, rel)
        if doc.id:
            existing = _find_id(conn, doc.id)
            if existing and existing != rel:
                for p in (existing, rel):
                    _add_warning(
                        conn, p, "duplicate_id",
                        f"ID {doc.id} duplicado em {existing} e {rel} — conflito",
                    )
            elif top == "requirements":
                _insert_requirement(conn, doc, rel)
            elif top == "testcases":
                _insert_testcase(conn, doc, rel)
            elif top == "defects":
                _insert_defect(conn, doc, rel)
            elif top == "todos":
                _insert_todo(conn, doc, rel)
            elif top == "meetings":
                _insert_meeting(conn, doc, rel)
            m = _ID_RE.match(doc.id)
            if m:
                ws.bump_counter_to(m.group(1), int(m.group(2)))
    if rel.split("/", 1)[0] in ("requirements", "testcases"):
        _recompute_effective_squads(conn)  # herança pode mudar com o arquivo editado
    conn.commit()


def _find_id(conn: sqlite3.Connection, entity_id: str) -> str | None:
    for table in ("requirements", "testcases", "defects", "todos", "meetings"):
        row = conn.execute(f"SELECT path FROM {table} WHERE id = ?", (entity_id,)).fetchone()
        if row:
            return row["path"]
    return None


def _flush_doc_warnings(conn: sqlite3.Connection, doc: ParsedDoc, rel: str) -> None:
    for code, message in doc.warnings:
        _add_warning(conn, rel, code, message)


def _squad(doc: ParsedDoc) -> str | None:
    raw = doc.meta.get("squad")
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def _insert_requirement(conn: sqlite3.Connection, doc: ParsedDoc, rel: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO requirements"
        "(id, kind, title, epic_id, status, external_key, confluence_url, tags, path, mtime,"
        " squad, created)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            doc.id,
            str(doc.meta.get("kind", "")),
            str(doc.meta.get("title", "")),
            doc.meta.get("epic"),
            str(doc.meta.get("status", "active")),
            doc.meta.get("external_key"),
            doc.meta.get("confluence_url"),
            ",".join(_tags(doc)),
            rel,
            doc.path.stat().st_mtime,
            _squad(doc),
            str(doc.meta.get("created")) if doc.meta.get("created") else None,
        ),
    )


def _insert_testcase(conn: sqlite3.Connection, doc: ParsedDoc, rel: str) -> None:
    automation = doc.meta.get("automation") or {}
    squad = _squad(doc)
    conn.execute(
        "INSERT OR REPLACE INTO testcases"
        "(id, title, type, priority, status, story_id, path, mtime,"
        " automation_target, scenario_tag, external_key, squad, squad_effective, created)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            doc.id,
            str(doc.meta.get("title", "")),
            str(doc.meta.get("type", "manual")),
            str(doc.meta.get("priority", "medium")),
            str(doc.meta.get("status", "draft")),
            doc.meta.get("story"),
            rel,
            doc.path.stat().st_mtime,
            automation.get("target") if isinstance(automation, dict) else None,
            automation.get("scenario_tag") if isinstance(automation, dict) else None,
            doc.meta.get("external_key"),
            squad,
            squad,  # placeholder; a herança é resolvida por _recompute_effective_squads
            str(doc.meta.get("created")) if doc.meta.get("created") else None,
        ),
    )
    for tag in _tags(doc):
        conn.execute("INSERT INTO tc_tags(testcase_id, tag) VALUES (?,?)", (doc.id, tag))


def _recompute_effective_squads(conn: sqlite3.Connection) -> None:
    """squad efetivo do CT: próprio → da story → do epic da story (SQL único).

    Materializado para manter os filtros downstream triviais
    (`WHERE squad_effective = ?`). Chamado ao fim do reindex e sempre que um
    requisito ou test case muda no incremental.
    """
    conn.execute(
        "UPDATE testcases SET squad_effective = COALESCE("
        "  NULLIF(squad, ''),"
        "  (SELECT NULLIF(s.squad, '') FROM requirements s WHERE s.id = testcases.story_id),"
        "  (SELECT NULLIF(e.squad, '') FROM requirements e WHERE e.id = ("
        "     SELECT s2.epic_id FROM requirements s2 WHERE s2.id = testcases.story_id))"
        ")"
    )


def _insert_defect(conn: sqlite3.Connection, doc: ParsedDoc, rel: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO defects"
        "(id, title, status, severity, testcase_id, execution_id, external_key, path,"
        " opened_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (
            doc.id,
            str(doc.meta.get("title", "")),
            str(doc.meta.get("status", "open")),
            doc.meta.get("severity"),
            doc.meta.get("testcase"),
            doc.meta.get("execution"),
            doc.meta.get("external_key"),
            rel,
            str(doc.meta.get("opened")) if doc.meta.get("opened") else None,
        ),
    )


def _insert_todo(conn: sqlite3.Connection, doc: ParsedDoc, rel: str) -> None:
    raw_links = doc.meta.get("links") or []
    if isinstance(raw_links, str):
        raw_links = [raw_links]
    links = ",".join(str(link) for link in raw_links)
    conn.execute(
        "INSERT OR REPLACE INTO todos"
        "(id, title, status, due, squad, links, created, path, mtime)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (
            doc.id,
            str(doc.meta.get("title", "")),
            str(doc.meta.get("status", "open")),
            str(doc.meta.get("due")) if doc.meta.get("due") else None,
            (str(doc.meta.get("squad")).strip() or None) if doc.meta.get("squad") else None,
            links,
            str(doc.meta.get("created")) if doc.meta.get("created") else None,
            rel,
            doc.path.stat().st_mtime,
        ),
    )


def _insert_meeting(conn: sqlite3.Connection, doc: ParsedDoc, rel: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO meetings(id, title, date, summary, path, mtime)"
        " VALUES (?,?,?,?,?,?)",
        (
            doc.id,
            str(doc.meta.get("title", "")),
            str(doc.meta.get("date")) if doc.meta.get("date") else None,
            str(doc.meta.get("summary")) if doc.meta.get("summary") else None,
            rel,
            doc.path.stat().st_mtime,
        ),
    )


def _drop_execution_rows(conn: sqlite3.Connection, rel: str) -> None:
    row = conn.execute("SELECT id FROM executions WHERE path = ?", (rel,)).fetchone()
    if row:
        conn.execute("DELETE FROM results WHERE execution_id = ?", (row["id"],))
        conn.execute("DELETE FROM result_events WHERE execution_id = ?", (row["id"],))
        conn.execute("DELETE FROM evidences WHERE execution_id = ?", (row["id"],))
    conn.execute("DELETE FROM executions WHERE path = ?", (rel,))


def _index_execution(
    conn: sqlite3.Connection,
    ws: Workspace,
    path: Path,
    rel: str,
    max_by_prefix: dict[str, int],
) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        _add_warning(conn, rel, "invalid_execution", f"{path.name}: {exc}")
        return
    exec_id = data.get("id")
    if not exec_id:
        _add_warning(conn, rel, "invalid_execution", f"{path.name}: sem campo 'id'")
        return
    m = _ID_RE.match(str(exec_id))
    if m:
        prefix, num = m.group(1), int(m.group(2))
        max_by_prefix[prefix] = max(max_by_prefix.get(prefix, 0), num)
        ws.bump_counter_to(prefix, num)
    conn.execute(
        "INSERT OR REPLACE INTO executions"
        "(id, name, owner, sprint, environment, origin, status, created_at, closed_at, path,"
        " squad)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            exec_id,
            data.get("name"),
            data.get("owner"),
            data.get("sprint"),
            data.get("environment"),
            data.get("origin", "manual"),
            data.get("status", "draft"),
            data.get("created_at"),
            data.get("closed_at"),
            rel,
            (str(data.get("squad")).strip() or None) if data.get("squad") else None,
        ),
    )
    for result in data.get("results") or []:
        conn.execute(
            "INSERT OR REPLACE INTO results"
            "(execution_id, testcase_id, status, executed_at, duration_seconds)"
            " VALUES (?,?,?,?,?)",
            (
                exec_id,
                result.get("testcase_id"),
                result.get("status", "pending"),
                result.get("executed_at"),
                result.get("duration_seconds"),
            ),
        )
        for evidence in result.get("evidences") or []:
            conn.execute(
                "INSERT INTO evidences"
                "(execution_id, testcase_id, path, sha256, mime, captured_at)"
                " VALUES (?,?,?,?,?,?)",
                (
                    exec_id,
                    result.get("testcase_id"),
                    evidence.get("path"),
                    evidence.get("sha256"),
                    evidence.get("mime"),
                    evidence.get("captured_at"),
                ),
            )
    for event in data.get("history") or []:
        if event.get("event") == "result" and event.get("testcase_id"):
            conn.execute(
                "INSERT INTO result_events(execution_id, testcase_id, status, at)"
                " VALUES (?,?,?,?)",
                (exec_id, event["testcase_id"], event.get("to"), event.get("at")),
            )


def _relational_checks(conn: sqlite3.Connection) -> None:
    """Integridade entre entidades — sempre warning, nunca bloqueio."""
    for row in conn.execute(
        "SELECT r.id, r.epic_id, r.path FROM requirements r"
        " WHERE r.kind = 'story' AND r.epic_id IS NOT NULL"
        " AND r.epic_id NOT IN (SELECT id FROM requirements WHERE kind = 'epic')"
    ).fetchall():
        _add_warning(
            conn, row["path"], "missing_epic",
            f"{row['id']}: epic '{row['epic_id']}' não existe",
        )
    for row in conn.execute(
        "SELECT t.id, t.story_id, t.path FROM testcases t"
        " WHERE t.story_id IS NOT NULL"
        " AND t.story_id NOT IN (SELECT id FROM requirements WHERE kind = 'story')"
    ).fetchall():
        _add_warning(
            conn, row["path"], "missing_story",
            f"{row['id']}: story '{row['story_id']}' não existe",
        )
