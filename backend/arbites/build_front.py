"""O build do frontend está velho? (change 0182)

`frontend/dist/` não é versionado — é artefato, e versioná-lo encheria o
histórico de bundle minificado. A consequência é que `git pull` atualiza o
CÓDIGO e não o que o servidor entrega: quem pula o `npm run build` continua
vendo a interface antiga, sem nada dizendo isso. Um conserto que "não
apareceu" é indistinguível de um conserto que não funcionou.

É o mesmo defeito de fundo de outras três changes desta linha (0157, 0165,
0170): a diferença entre o ambiente de quem desenvolve e o de quem usa,
acontecendo em silêncio.

A comparação é por mtime, e mtime não é ordem de commit: um `git pull` pode
deixar o fonte com data mais nova sem nada ter mudado de fato. Por isso isto
é AVISO, nunca recusa — errar para o lado de avisar à toa custa uma linha;
errar para o outro custa a tarde de quem está depurando a tela errada.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# O que, mudando, exige um build novo. `src/` é o óbvio; os outros três
# mudam o bundle sem ninguém lembrar.
FONTES = ("src", "index.html", "package.json", "vite.config.ts")
IGNORAR = {"node_modules", "dist", ".vite", "__pycache__"}


def _mais_recente(caminho: Path) -> float:
    if caminho.is_file():
        return caminho.stat().st_mtime
    if not caminho.is_dir():
        return 0.0
    recente = 0.0
    for raiz, pastas, arquivos in os.walk(caminho):
        pastas[:] = [p for p in pastas if p not in IGNORAR and not p.startswith(".")]
        for nome in arquivos:
            try:
                recente = max(recente, (Path(raiz) / nome).stat().st_mtime)
            except OSError:
                continue
    return recente


def raiz_do_frontend(dist: str | os.PathLike[str]) -> Path:
    """A pasta do frontend a partir do `dist` que está sendo servido."""
    return Path(dist).resolve().parent


def estado(dist: str | os.PathLike[str]) -> dict[str, Any]:
    """`{servindo, existe, fonte_em, build_em, desatualizado, motivo}`.

    Sem a pasta do fonte ao lado — o caso do container, que copia só o
    `dist` — não há o que comparar, e a resposta é "não sei", não
    "está velho".
    """
    destino = Path(dist)
    if not destino.is_dir():
        return {"servindo": str(destino), "existe": False,
                "desatualizado": False,
                "motivo": "nenhum build em dist/: a interface não é servida"}
    raiz = raiz_do_frontend(destino)
    fontes = [raiz / nome for nome in FONTES if (raiz / nome).exists()]
    if not fontes:
        return {"servindo": str(destino), "existe": True,
                "desatualizado": False,
                "motivo": "sem o código-fonte ao lado; nada a comparar"}
    fonte_em = max(_mais_recente(f) for f in fontes)
    build_em = _mais_recente(destino)
    return {
        "servindo": str(destino),
        "existe": True,
        "fonte_em": fonte_em,
        "build_em": build_em,
        "desatualizado": fonte_em > build_em,
        "motivo": "",
    }


def comando(dist: str | os.PathLike[str]) -> str:
    """O comando exato, com o caminho que esta instalação usa."""
    raiz = raiz_do_frontend(dist)
    return f"npm --prefix {raiz} run build"


def aviso(dist: str | os.PathLike[str]) -> dict[str, Any] | None:
    """O aviso no formato da lista de problemas, ou None quando está em dia."""
    situacao = estado(dist)
    if not situacao.get("desatualizado"):
        return None
    from datetime import datetime, timezone

    return {
        "source_path": situacao["servindo"],
        "code": "frontend_desatualizado",
        "message": (
            "o código do frontend é mais recente que o build servido em"
            " dist/ — a tela que você está vendo é a anterior."
            f" Rode: {comando(dist)}"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
