"""Ponto de entrada do servidor MCP: `python -m arbites.mcp` (change 0146).

`--diagnostico` imprime por que ele não está servindo, em TEXTO. Existe porque
o cliente MCP mostra "Connection closed" e nada mais quando o servidor falha,
e esse erro não é um diagnóstico — é o cliente dizendo que não sabe (0200).
"""

import asyncio
import sys

from .mcp_server import diagnostico, main

if __name__ == "__main__":
    if "--diagnostico" in sys.argv:
        for linha in asyncio.run(diagnostico()):
            print(linha)
    else:
        asyncio.run(main())
