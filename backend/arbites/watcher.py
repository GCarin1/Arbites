"""Watcher — casca fina sobre watchdog que delega para reindex_file.

Toda a lógica vive em `indexer.reindex_file`; aqui só há roteamento de
eventos, então os testes exercitam o indexer diretamente (determinístico).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .indexer import reindex_file
from .workspace import Workspace

WATCHED_DIRS = ("requirements", "testcases", "defects")


class _Handler(FileSystemEventHandler):
    def __init__(self, ws: Workspace, conn: sqlite3.Connection):
        self.ws = ws
        self.conn = conn

    def dispatch(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        for raw in {str(event.src_path), str(getattr(event, "dest_path", "") or "")}:
            if not raw or not raw.endswith(".md"):
                continue
            path = Path(raw)
            try:
                rel = path.resolve().relative_to(self.ws.root)
            except ValueError:
                continue
            if rel.parts and rel.parts[0] in WATCHED_DIRS:
                reindex_file(self.ws, self.conn, path)


def start_watcher(ws: Workspace, conn: sqlite3.Connection) -> Observer:
    observer = Observer()
    observer.schedule(_Handler(ws, conn), str(ws.root), recursive=True)
    observer.daemon = True
    observer.start()
    return observer
