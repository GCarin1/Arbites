"""Ponto de entrada do servidor MCP: `python -m arbites.mcp` (change 0146).

`--diagnostico` imprime por que ele não está servindo, em TEXTO. Existe porque
o cliente MCP mostra "Connection closed" e nada mais quando o servidor falha,
e esse erro não é um diagnóstico — é o cliente dizendo que não sabe (0200).

`--url` e `--token` existem porque o ambiente do TERMINAL não é o ambiente do
servidor: o bloco `env` do `mcp.json` só chega ao processo que o cliente
lança. Sem poder passá-los na mão, o diagnóstico rodado à mão responderia
sempre "NAO DEFINIDO" e mandaria procurar o problema errado (0201).
"""

import asyncio
import sys

from .mcp_server import diagnostico, main


def _valor(nome: str) -> str | None:
    """`--nome valor`, sem argparse: este módulo é lançado por um cliente MCP
    e não pode ganhar `--help` nem sair com erro por argumento estranho."""
    if nome in sys.argv:
        i = sys.argv.index(nome)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


if __name__ == "__main__":
    if "--diagnostico" in sys.argv:
        for linha in asyncio.run(
            diagnostico(_valor("--url"), _valor("--token"))
        ):
            print(linha)
    else:
        asyncio.run(main())
