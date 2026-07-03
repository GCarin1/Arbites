import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from arbites.api import create_app  # noqa: E402
from arbites.indexer import connect, reindex_full  # noqa: E402
from arbites.workspace import Workspace  # noqa: E402


@pytest.fixture()
def ws(tmp_path) -> Workspace:
    workspace = Workspace(tmp_path / "workspace")
    workspace.ensure()
    return workspace


@pytest.fixture()
def client(ws):
    app = create_app(ws.root, watch=False)
    with TestClient(app) as test_client:
        test_client.ws = ws
        yield test_client


def make_md(path, meta: dict, body: str = "") -> None:
    """Escreve um .md com frontmatter à mão (simula edição externa)."""
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{yaml.safe_dump(meta, allow_unicode=True)}---\n\n{body}",
        encoding="utf-8",
    )


@pytest.fixture()
def indexed(ws):
    conn = connect(ws)
    reindex_full(ws, conn)
    return conn
