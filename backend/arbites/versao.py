"""Qual código este processo está rodando? (change 0184)

"Atualizei e o erro continua" tem duas leituras — o conserto não funcionou,
ou o conserto não está rodando — e nada aqui distinguia as duas. `__version__`
é fixo em "0.1.0" desde sempre, então `/health` respondia a mesma coisa para
qualquer commit.

A resposta vem do git quando há um checkout, porque é a única fonte que não
mente: um número que alguém precisa lembrar de incrementar fica para trás
exatamente na hora em que ele importaria. Sem git (imagem de container,
cópia baixada), diz isso em vez de inventar.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import __version__


def _raiz() -> Path:
    return Path(__file__).resolve().parents[2]


def _git(*args: str) -> str | None:
    try:
        saida = subprocess.run(
            ["git", "-C", str(_raiz()), *args],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if saida.returncode != 0:
        return None
    return saida.stdout.strip() or None


@lru_cache(maxsize=1)
def identidade() -> dict[str, Any]:
    """Calculada uma vez: o processo não muda de código enquanto vive."""
    commit = _git("rev-parse", "--short", "HEAD")
    if not commit:
        return {"version": __version__, "commit": None, "branch": None,
                "commit_at": None, "dirty": None,
                "origem": "sem checkout git ao lado; só a versão do pacote"}
    return {
        "version": __version__,
        "commit": commit,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit_at": _git("log", "-1", "--format=%cI"),
        # Alterações locais não commitadas mudam o que roda: omitir isso faria
        # o commit mentir por semelhança.
        "dirty": bool(_git("status", "--porcelain")),
        "origem": "git",
    }


def linha() -> str:
    """Uma linha para o terminal — onde a pergunta costuma ser feita."""
    dados = identidade()
    if not dados.get("commit"):
        return f"Arbites {dados['version']} ({dados['origem']})"
    quando = dados.get("commit_at") or ""
    try:
        quando = datetime.fromisoformat(quando).astimezone(
            timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    except ValueError:
        quando = quando[:10]
    sujo = " +alterações locais" if dados.get("dirty") else ""
    return (f"Arbites {dados['version']} · {dados['branch']}@{dados['commit']}"
            f" de {quando}{sujo}")
