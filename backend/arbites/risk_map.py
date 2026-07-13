"""Mapa de Risco — cruza churn de git (mudanças recentes por arquivo) com
sinais de defeito (commits cuja mensagem referencia um DF-ID real do índice)
e a cobertura de automação do repo, para apontar onde o código muda mais,
quebra mais e é testado menos. Lê repositórios locais configurados em
`arbites.yaml` (`risk_repos`: `name` + `local_path`, mesmo padrão de
`automation_targets`) via `git log` (subprocess, read-only — nunca escreve
no repositório do usuário).
"""

from __future__ import annotations

import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .metrics import automation_report

_GIT_TIMEOUT_SECONDS = 15
_DEFAULT_SINCE_DAYS = 90
_DEFAULT_TOP_N = 30


def _git_log(local_path: Path, since_days: int) -> list[tuple[str, list[str]]]:
    """[(mensagem_do_commit, [arquivos_tocados]), ...], mais recente primeiro.

    NUL (`\\x00`) separa commits para não colidir com quebras de linha em
    mensagens multi-linha; `git log` é chamado read-only (nenhum comando de
    escrita), com timeout para não travar a request num repo gigante/lento.
    """
    try:
        proc = subprocess.run(
            ["git", "log", f"--since={since_days}.days", "--name-only",
             "--pretty=format:%x00%s"],
            cwd=str(local_path), capture_output=True, text=True,
            timeout=_GIT_TIMEOUT_SECONDS, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    commits: list[tuple[str, list[str]]] = []
    for block in proc.stdout.split("\x00")[1:]:
        block_lines = block.strip("\n").split("\n")
        message = block_lines[0]
        files = [f for f in block_lines[1:] if f.strip()]
        commits.append((message, files))
    return commits


def _defect_re(defect_prefix: str) -> re.Pattern[str]:
    """Regex de menção a defeito com o prefixo CONFIGURADO do workspace
    (`id_prefixes.defect`) — hardcodar `DF-` quebraria a correlação
    commit↔defeito em workspaces com prefixo customizado."""
    return re.compile(rf"\b{re.escape(defect_prefix)}-\d+\b")


def scan_repo(
    conn: sqlite3.Connection,
    name: str,
    local_path: str,
    since_days: int = _DEFAULT_SINCE_DAYS,
    top_n: int = _DEFAULT_TOP_N,
    defect_prefix: str = "DF",
    pass_rate_by_repo: dict[str, float | None] | None = None,
) -> dict[str, Any]:
    """Escaneia UM repo configurado; nunca levanta — path inválido vira `error`."""
    path = Path(local_path)
    if not local_path or not path.is_dir():
        return {
            "repo": name,
            "error": f"local_path não encontrado: {local_path or '(vazio)'}",
            "total_commits": 0,
            "files": [],
            "automation_pass_rate": None,
        }

    commits = _git_log(path, since_days)
    known_defects = {r["id"] for r in conn.execute("SELECT id FROM defects")}
    df_re = _defect_re(defect_prefix)

    churn: dict[str, int] = {}
    defect_commits: dict[str, int] = {}
    for message, files in commits:
        mentions_known_defect = any(m in known_defects for m in df_re.findall(message))
        for f in files:
            churn[f] = churn.get(f, 0) + 1
            if mentions_known_defect:
                defect_commits[f] = defect_commits.get(f, 0) + 1

    files_out = [
        {"path": f, "churn": c, "defect_commits": defect_commits.get(f, 0)}
        for f, c in churn.items()
    ]
    files_out.sort(key=lambda r: (r["churn"], r["defect_commits"]), reverse=True)

    return {
        "repo": name,
        "error": None,
        "total_commits": len(commits),
        "files": files_out[:top_n],
        "automation_pass_rate": (pass_rate_by_repo or {}).get(name),
    }


def build(
    conn: sqlite3.Connection,
    repos: list[dict[str, Any]],
    since_days: int = _DEFAULT_SINCE_DAYS,
    defect_prefix: str = "DF",
    name_pattern: str | None = None,
) -> dict[str, Any]:
    # o report de automação é um só para o workspace inteiro — computar uma
    # vez aqui (com o name_pattern configurado, mesmo padrão do endpoint
    # /metrics/automation) em vez de uma vez por repo dentro do scan
    arep = automation_report(conn, name_pattern)
    pass_rate_by_repo = {r["repo"]: r["pass_rate"] for r in arep["by_repo"]}
    return {
        "since_days": since_days,
        "repos": [
            scan_repo(
                conn, str(r.get("name", "")), str(r.get("local_path", "")),
                since_days, defect_prefix=defect_prefix,
                pass_rate_by_repo=pass_rate_by_repo,
            )
            for r in repos
        ],
    }
