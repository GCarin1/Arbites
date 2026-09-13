"""Versionamento do workspace com git — histórico, comparação e volta atrás.

O workspace já é filesystem (ADR 0001) e o caso de teste já é um `.md` em
disco. O que falta a ele é o que todo repositório de código tem há trinta
anos: saber o que mudou, quando, por quem, e poder voltar. Isso não pede
banco novo nem formato novo — pede `git`, que é a tecnologia certa para
exatamente este problema.

Duas regras moldam o módulo:

**A unidade de commit é a ação semântica, não a gravação.** Criar um caso,
editar, mover e excluir viram um commit cada, com a mensagem dizendo o que
aconteceu. Um commit por gravação encheria o histórico de ruído e faria a
comparação entre versões perder o sentido.

**Registro nunca derruba escrita.** Se o git não está instalado, se o
`git init` falha, se o commit falha — a operação do usuário continua. Um
histórico incompleto é ruim; perder o caso de teste que a pessoa acabou de
escrever porque o git tossiu é inaceitável.
"""

from __future__ import annotations

import logging
import subprocess
import threading
from pathlib import Path
from typing import Any

from .workspace import Workspace

log = logging.getLogger("arbites")

_GIT_TIMEOUT_SECONDS = 15

# O git tem UM lock por repositório: duas escritas simultâneas disputam o
# `index.lock` e a perdedora falha. Uma fila no processo transforma a disputa
# em espera, que é o que ela deveria ter sido desde o início (change 0120).
_git_lock = threading.Lock()

# O índice é descartável (ADR 0001) e a lixeira é estado local: nenhum dos
# dois entra no histórico. Segredos nunca deveriam estar aqui, mas se
# estiverem, não é o git que vai carregá-los para fora.
GITIGNORE = """\
# Índice descartável e estado local do Arbites (ADR 0001) — reconstruível
# a partir dos arquivos, e por isso fora do histórico.
.arbites/
*.db
*.db-journal

# Segredos jamais versionados.
.env
*.key
"""

_IDENTITY_FALLBACK = ("Arbites", "arbites@local")


class GitUnavailable(Exception):
    """O git não respondeu. Quem chama decide seguir sem histórico."""


def _run(
    ws: Workspace, args: list[str], *, author: tuple[str, str] | None = None
) -> str:
    """Roda um comando git no workspace e devolve o stdout.

    A identidade vai por `-c` em vez de `git config`: assim o commit é
    assinado com o autor da sessão sem tocar na configuração global da
    máquina de quem hospeda a instância.
    """
    name, email = author or _IDENTITY_FALLBACK
    command = [
        "git",
        "-c", f"user.name={name}",
        "-c", f"user.email={email}",
        "-c", "commit.gpgsign=false",
        *args,
    ]
    try:
        with _git_lock:
            proc = subprocess.run(
                command, cwd=str(ws.root), capture_output=True, text=True,
                timeout=_GIT_TIMEOUT_SECONDS, check=True,
            )
    except subprocess.CalledProcessError as exc:
        raise GitUnavailable(exc.stderr.strip() or str(exc)) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitUnavailable(str(exc)) from exc
    return proc.stdout


def is_repo(ws: Workspace) -> bool:
    return (ws.root / ".git").exists()


def ensure_repo(ws: Workspace) -> bool:
    """`git init` + `.gitignore` na primeira escrita. Devolve se há repo."""
    if is_repo(ws):
        return True
    try:
        _run(ws, ["init", "-q"])
        gitignore = ws.root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(GITIGNORE, encoding="utf-8")
        _run(ws, ["add", "--", ".gitignore"])
        _run(ws, ["commit", "-q", "-m", "chore: workspace sob versionamento"])
        return True
    except GitUnavailable:
        return False


def _author_of(email: str | None) -> tuple[str, str]:
    if not email:
        return _IDENTITY_FALLBACK
    return (email.split("@")[0] or email, email)


def commit_paths(
    ws: Workspace, paths: list[Path], message: str, email: str | None = None
) -> str | None:
    """Commita exatamente os caminhos de UMA ação. Devolve o sha, ou None
    quando não havia nada para gravar (ou quando o git não está disponível —
    e aí a operação do usuário segue sem histórico, de propósito)."""
    if not ensure_repo(ws):
        return None
    relatives = [ws.relpath(p) for p in paths]
    try:
        # `-A` pega o arquivo que sumiu (exclusão) junto com o que apareceu
        _run(ws, ["add", "-A", "--", *relatives])
        if not _run(ws, ["diff", "--cached", "--name-only", "--", *relatives]).strip():
            return None
        _run(
            ws,
            ["commit", "-q", "-m", message, "--only", "--", *relatives],
            author=_author_of(email),
        )
        return _run(ws, ["rev-parse", "HEAD"]).strip()
    except GitUnavailable as exc:
        # A escrita do usuário continua de pé — mas a ausência no histórico
        # precisa ser explicável, e não misteriosa (change 0120).
        log.warning(
            "versionamento: commit nao gravado (%s) para %s — %s",
            message, ", ".join(relatives), exc,
        )
        return None


def commit_external_edits(ws: Workspace, rel: str) -> str | None:
    """Edição feita por fora (Obsidian) vira commit de autoria externa.

    O arquivo é a fonte da verdade; quem edita a fonte da verdade não
    deveria precisar pedir licença à interface para aparecer no histórico.
    """
    if not ensure_repo(ws):
        return None
    try:
        pending = _run(ws, ["status", "--porcelain", "--", rel]).strip()
    except GitUnavailable:
        return None
    if not pending:
        return None
    return commit_paths(
        ws, [ws.root / rel], f"edicao externa: {rel}", "externo@workspace"
    )


def history(ws: Workspace, rel: str, limit: int = 50) -> list[dict[str, Any]]:
    """Versões de UM arquivo, mais recente primeiro.

    `--follow` para que renomear (mover de pasta) não corte o histórico ao
    meio — mover um caso preserva o ID, e deveria preservar o passado também.
    """
    if not is_repo(ws):
        return []
    try:
        out = _run(ws, [
            "log", f"-{limit}", "--follow", "--date=iso-strict",
            "--pretty=format:%H%x1f%an%x1f%ae%x1f%ad%x1f%s", "--", rel,
        ])
    except GitUnavailable:
        return []
    versions = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, name, email, when, subject = line.split("\x1f")
        versions.append({
            "sha": sha, "short": sha[:8], "author": name, "email": email,
            "at": when, "message": subject,
        })
    return versions


def content_at(ws: Workspace, sha: str, rel: str) -> str:
    """Conteúdo do arquivo naquele commit."""
    return _run(ws, ["show", f"{sha}:{rel}"])


def diff(ws: Workspace, rel: str, a: str, b: str | None = None) -> str:
    """Comparação unificada entre duas versões; `b` vazio = árvore de trabalho."""
    args = ["diff", a] + ([b] if b else []) + ["--", rel]
    return _run(ws, args)


def restore(
    ws: Workspace, sha: str, rel: str, email: str | None = None
) -> str | None:
    """Devolve o conteúdo de uma versão anterior gravando um commit NOVO.

    Restaurar é um evento do projeto, não um desmentido: o histórico entre a
    versão restaurada e hoje continua lá para quem for entender por quê.
    """
    content = content_at(ws, sha, rel)
    path = ws.root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return commit_paths(ws, [path], f"restaura {rel} para {sha[:8]}", email)
