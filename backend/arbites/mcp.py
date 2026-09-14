"""Ponto de entrada do servidor MCP: `python -m arbites.mcp` (change 0146)."""

import asyncio

from .mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())
