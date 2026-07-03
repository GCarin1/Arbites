"""SC8 — reindex completo < 5 s para 2.000 CTs (spec indexing, critério 2)."""

import time

from conftest import make_md

from arbites.indexer import connect, reindex_full


def test_full_reindex_2000_testcases_under_5_seconds(ws):
    body = (
        "## Objetivo\n\nValidar algo.\n\n## Passos\n\n1. Abrir\n2. Agir\n3. Conferir\n\n"
        "## Resultado esperado\n\nOk.\n"
    )
    for i in range(1, 2001):
        make_md(
            ws.root / "testcases" / f"grupo{i % 20}" / f"CT-{i:04d}-caso.md",
            {
                "id": f"CT-{i:04d}",
                "title": f"Caso {i}",
                "type": "manual",
                "priority": "medium",
                "status": "ready",
                "tags": ["regression"],
            },
            body,
        )
    conn = connect(ws)
    started = time.perf_counter()
    stats = reindex_full(ws, conn)
    elapsed = time.perf_counter() - started
    assert stats["testcases"] == 2000
    assert elapsed < 5.0, f"reindex levou {elapsed:.2f}s (limite 5s)"
