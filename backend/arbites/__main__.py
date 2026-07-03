"""Entrada CLI: `python -m arbites serve` (API + UI) e `python -m arbites reindex`."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(prog="arbites")
    parser.add_argument(
        "command", nargs="?", default="serve", choices=["serve", "reindex"]
    )
    parser.add_argument(
        "--workspace",
        default=os.environ.get("ARBITES_WORKSPACE", "workspace"),
        help="caminho do workspace (default: ./workspace ou $ARBITES_WORKSPACE)",
    )
    parser.add_argument("--port", type=int, default=8347)
    args = parser.parse_args()

    if args.command == "reindex":
        from .indexer import connect, reindex_full
        from .workspace import Workspace

        ws = Workspace(args.workspace)
        ws.ensure()
        stats = reindex_full(ws, connect(ws))
        print(stats)
        return

    import uvicorn

    os.environ["ARBITES_WORKSPACE"] = args.workspace
    from .api import create_app

    uvicorn.run(create_app(args.workspace), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
