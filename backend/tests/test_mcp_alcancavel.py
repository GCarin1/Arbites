"""O cliente MCP precisa ACHAR o pacote (change 0201).

`python -m arbites.mcp` só encontrava `arbites` quando o processo nascia
dentro de `backend/`. O cliente MCP não nasce ali — ele lança o comando a
partir da pasta dele. O Python respondia `No module named arbites` em stderr,
que a maioria dos clientes não exibe, e sobrava `Connection closed`: o mesmo
erro genérico de sempre, agora por outro motivo.

Reproduzido com um cliente MCP de verdade antes de consertar, e a causa era a
documentação: o `mcp.json` do README mostrava o comando sem `cwd` nenhum.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _de_fora(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    """Roda sem PYTHONPATH — a condição real do processo que o cliente
    lança, e a única em que o defeito aparecia."""
    ambiente = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run([sys.executable, *args], cwd=cwd, env=ambiente,
                          capture_output=True, text=True, timeout=120)


def test_com_cwd_no_backend_o_modulo_e_encontrado():
    """O caminho documentado no README, agora com `cwd`."""
    saida = _de_fora(["-c", "import arbites.mcp"], str(RAIZ))

    assert saida.returncode == 0, saida.stderr


def test_o_projeto_declara_como_ser_instalado():
    """A alternativa que dispensa o `cwd`: instalado, o comando funciona de
    qualquer pasta. Sem `pyproject.toml` isso não era possível."""
    dados = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))

    assert dados["project"]["name"] == "arbites"
    assert "arbites.__main__:main" in dados["project"]["scripts"].values()


def test_a_versao_exigida_aceita_o_python_que_roda_a_suite():
    """Exigir uma versão acima da que roda o produto troca um erro por outro:
    "não acha o pacote" vira "versão errada", e isso não é progresso."""
    dados = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    exigido = dados["project"]["requires-python"].lstrip(">=")

    atual = (sys.version_info.major, sys.version_info.minor)
    assert atual >= tuple(int(p) for p in exigido.split(".")[:2])


def test_o_diagnostico_aponta_o_conserto_quando_o_pacote_nao_alcanca():
    """O diagnóstico roda de dentro do projeto, onde SEMPRE funciona — então
    ele precisa aferir de fora, senão daria um "ok" que não vale nada."""
    from arbites.diagnostico import secao_mcp

    saida = "\n".join(secao_mcp())

    assert "[servidor MCP]" in saida
    # Um dos dois desfechos, e os dois são informativos: instalado, ou o
    # comando exato para resolver.
    assert ("funciona de qualquer pasta" in saida
            or ("pip install -e" in saida and "cwd" in saida))


def test_o_readme_documenta_o_cwd():
    """A documentação era a causa direta: mostrava o comando sem `cwd`, e
    quem copiava caía no erro genérico."""
    readme = (RAIZ.parent / "README.md").read_text(encoding="utf-8")
    bloco = readme[readme.index('"mcpServers"'):][:600]

    assert '"cwd"' in bloco
    assert "pip install -e backend" in readme
