"""Autenticação — contas, sessões, lockout (ADR 0011).

Este módulo é o único ponto de acesso ao `.arbites/auth.db`: um SQLite
**durável**, separado do índice descartável `.arbites/index.db`. Nenhum
caminho de indexação, watcher ou reconstrução encosta neste arquivo — o que
está aqui não pode ser reconstruído a partir do disco.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from .workspace import Workspace

# -- política ---------------------------------------------------------------

MIN_PASSWORD_LEN = 12
SESSION_COOKIE = "arbites_session"
IDLE_TIMEOUT = timedelta(hours=12)
ABSOLUTE_TIMEOUT = timedelta(days=7)
LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW = timedelta(minutes=15)

ROLES = ("admin", "editor", "viewer")
STATUSES = ("pending", "active", "disabled", "rejected")

_hasher = PasswordHasher()

# Hash descartável para igualar o custo de tempo quando o e-mail não existe:
# sem isso, "conta inexistente" responde mais rápido que "senha errada" e o
# atacante enumera contas pelo relógio.
_DUMMY_HASH = _hasher.hash("arbites-dummy-password-for-timing")


class AuthError(Exception):
    """Falha de autenticação com código estável para a API."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


# -- banco ------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    email                TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name                 TEXT NOT NULL DEFAULT '',
    password_hash        TEXT NOT NULL,
    role                 TEXT NOT NULL DEFAULT 'viewer',
    status               TEXT NOT NULL DEFAULT 'pending',
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at           TEXT NOT NULL,
    last_login_at        TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash   TEXT PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    ip           TEXT NOT NULL DEFAULT '',
    user_agent   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS login_attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT NOT NULL,
    ip         TEXT NOT NULL DEFAULT '',
    user_agent TEXT NOT NULL DEFAULT '',
    ok         INTEGER NOT NULL,
    at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_email_at ON login_attempts(email, at);
CREATE INDEX IF NOT EXISTS idx_attempts_ip_at ON login_attempts(ip, at);

CREATE TABLE IF NOT EXISTS activity (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    at          TEXT NOT NULL,
    user_id     INTEGER,
    user_email  TEXT NOT NULL DEFAULT '',
    method      TEXT NOT NULL,
    path        TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    ip          TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_activity_at ON activity(at);
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity(user_email, at);

CREATE TABLE IF NOT EXISTS agent_tokens (
    token_hash   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TEXT NOT NULL,
    last_used_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_agent_tokens_user ON agent_tokens(user_id);

CREATE TABLE IF NOT EXISTS switches (
    name       TEXT PRIMARY KEY,
    enabled    INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT ''
);
"""


def auth_db_path(ws: Workspace) -> str:
    return str(ws.arbites_dir / "auth.db")


def connect_auth(ws: Workspace) -> sqlite3.Connection:
    """Abre (e cria, se preciso) o banco de contas. Conexão própria: nunca a
    do índice."""
    ws.arbites_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(auth_db_path(ws), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# -- senha ------------------------------------------------------------------

def validate_password(password: str) -> None:
    if len(password or "") < MIN_PASSWORD_LEN:
        raise AuthError(
            422, "weak_password",
            "a senha precisa de pelo menos %d caracteres" % MIN_PASSWORD_LEN,
        )


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    """Verifica sempre, mesmo sem hash: o custo de tempo tem de ser o mesmo
    para conta inexistente e para senha errada."""
    target = stored_hash or _DUMMY_HASH
    try:
        _hasher.verify(target, password or "")
    except (Argon2Error, ValueError, TypeError):
        return False
    return stored_hash is not None


# -- usuários ---------------------------------------------------------------

def _row_to_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "status": row["status"],
        "must_change_password": bool(row["must_change_password"]),
        "created_at": row["created_at"],
        "last_login_at": row["last_login_at"],
    }


def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM users WHERE email = ? COLLATE NOCASE", ((email or "").strip(),)
    ).fetchone()


def get_user(conn: sqlite3.Connection, user_id: int) -> dict[str, Any] | None:
    return _row_to_user(
        conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    )


def list_users(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Contas com o número de sessões abertas — o painel precisa distinguir
    "pode entrar" de "está dentro agora"."""
    rows = conn.execute(
        "SELECT u.*, (SELECT COUNT(*) FROM sessions s WHERE s.user_id = u.id)"
        " AS open_sessions FROM users u ORDER BY u.created_at, u.id"
    ).fetchall()
    out = []
    for row in rows:
        user = _row_to_user(row)
        user["open_sessions"] = row["open_sessions"]
        out.append(user)
    return out


def count_users_by_status(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for row in conn.execute("SELECT status, COUNT(*) c FROM users GROUP BY status"):
        counts[row["status"]] = row["c"]
    return counts


def count_active_admins(conn: sqlite3.Connection, excluding: int | None = None) -> int:
    sql = "SELECT COUNT(*) FROM users WHERE role = 'admin' AND status = 'active'"
    params: tuple[Any, ...] = ()
    if excluding is not None:
        sql += " AND id != ?"
        params = (excluding,)
    return int(conn.execute(sql, params).fetchone()[0])


def create_user(
    conn: sqlite3.Connection,
    email: str,
    password: str,
    name: str = "",
    role: str = "viewer",
    status: str = "pending",
    must_change_password: bool = False,
) -> dict[str, Any]:
    email = (email or "").strip()
    if "@" not in email or len(email) < 3:
        raise AuthError(422, "invalid_email", "e-mail inválido")
    if role not in ROLES:
        raise AuthError(422, "invalid_role", "papel inválido: %s" % role)
    if status not in STATUSES:
        raise AuthError(422, "invalid_status", "status inválido: %s" % status)
    validate_password(password)
    if get_user_by_email(conn, email) is not None:
        raise AuthError(409, "email_taken", "já existe uma conta com esse e-mail")
    cur = conn.execute(
        "INSERT INTO users (email, name, password_hash, role, status,"
        " must_change_password, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (email, (name or "").strip(), hash_password(password), role, status,
         int(must_change_password), _iso(_now())),
    )
    conn.commit()
    return get_user(conn, int(cur.lastrowid))


def _guard_last_admin(conn: sqlite3.Connection, user: dict[str, Any]) -> None:
    if (user["role"] == "admin" and user["status"] == "active"
            and count_active_admins(conn, excluding=user["id"]) == 0):
        raise AuthError(
            409, "last_admin",
            "esta é a última conta admin ativa; promova outra antes",
        )


def set_status(conn: sqlite3.Connection, user_id: int, status: str) -> dict[str, Any]:
    if status not in STATUSES:
        raise AuthError(422, "invalid_status", "status inválido: %s" % status)
    user = get_user(conn, user_id)
    if user is None:
        raise AuthError(404, "user_not_found", "conta inexistente")
    if status != "active":
        _guard_last_admin(conn, user)
    conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
    conn.commit()
    if status != "active":
        # Deixar de estar ativo derruba o que estava aberto, na hora.
        revoke_user_sessions(conn, user_id)
    return get_user(conn, user_id)


def set_role(conn: sqlite3.Connection, user_id: int, role: str) -> dict[str, Any]:
    if role not in ROLES:
        raise AuthError(422, "invalid_role", "papel inválido: %s" % role)
    user = get_user(conn, user_id)
    if user is None:
        raise AuthError(404, "user_not_found", "conta inexistente")
    if role != "admin":
        _guard_last_admin(conn, user)
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    # O papel viajava na sessão resolvida; trocar sem derrubar deixaria a
    # sessão antiga operando com o papel velho.
    revoke_user_sessions(conn, user_id)
    return get_user(conn, user_id)


def set_password(
    conn: sqlite3.Connection, user_id: int, password: str,
    must_change: bool = False,
) -> None:
    validate_password(password)
    conn.execute(
        "UPDATE users SET password_hash = ?, must_change_password = ? WHERE id = ?",
        (hash_password(password), int(must_change), user_id),
    )
    conn.commit()
    # Troca de senha derruba TODAS as sessões: se a senha vazou, quem estava
    # dentro sai. Quem trocou recebe uma sessão nova (rotação) na API.
    revoke_user_sessions(conn, user_id)


# -- sessões ----------------------------------------------------------------

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def open_session(
    conn: sqlite3.Connection, user_id: int, ip: str = "", user_agent: str = ""
) -> str:
    """Devolve o token cru (vai para o cookie); o banco guarda só o SHA-256."""
    raw = secrets.token_urlsafe(32)  # 256 bits de entropia
    now = _iso(_now())
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, last_seen_at,"
        " ip, user_agent) VALUES (?, ?, ?, ?, ?, ?)",
        (_hash_token(raw), user_id, now, now, ip, (user_agent or "")[:300]),
    )
    conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now, user_id))
    conn.commit()
    return raw


def resolve_session(conn: sqlite3.Connection, raw: str | None) -> dict[str, Any] | None:
    """Valida o cookie e devolve o usuário, ou None. Expira por inatividade e
    por idade absoluta, e recusa conta que deixou de estar ativa."""
    if not raw:
        return None
    token_hash = _hash_token(raw)
    row = conn.execute(
        "SELECT created_at, last_seen_at, user_id FROM sessions WHERE token_hash = ?",
        (token_hash,),
    ).fetchone()
    if row is None:
        return None
    now = _now()
    if (now - _parse(row["last_seen_at"]) > IDLE_TIMEOUT
            or now - _parse(row["created_at"]) > ABSOLUTE_TIMEOUT):
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()
        return None
    user = get_user(conn, row["user_id"])
    if user is None or user["status"] != "active":
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()
        return None
    conn.execute(
        "UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
        (_iso(now), token_hash),
    )
    conn.commit()
    return user


def revoke_session(conn: sqlite3.Connection, raw: str | None) -> None:
    if not raw:
        return
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(raw),))
    conn.commit()


def revoke_user_sessions(conn: sqlite3.Connection, user_id: int) -> int:
    cur = conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    return cur.rowcount


def count_sessions(conn: sqlite3.Connection, user_id: int) -> int:
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    )


# -- tentativas e lockout ---------------------------------------------------

def record_attempt(
    conn: sqlite3.Connection, email: str, ip: str, ok: bool, user_agent: str = ""
) -> None:
    conn.execute(
        "INSERT INTO login_attempts (email, ip, user_agent, ok, at)"
        " VALUES (?, ?, ?, ?, ?)",
        ((email or "").strip(), ip, (user_agent or "")[:300], int(ok), _iso(_now())),
    )
    conn.commit()


def is_locked_out(conn: sqlite3.Connection, email: str, ip: str) -> bool:
    """Trava por conta E por IP: senão, um atacante distribui as tentativas
    entre e-mails e nunca dispara o limite.

    A contagem zera no último login bem-sucedido em vez de apagar linhas: o
    registro é append-only porque "cinco falhas e então um acerto" é
    exatamente a evidência que o painel de acessos precisa mostrar.
    """
    window_start = _iso(_now() - LOCKOUT_WINDOW)
    for column, value in (("email", (email or "").strip()), ("ip", ip)):
        if not value:
            continue
        last_success = conn.execute(
            "SELECT MAX(at) FROM login_attempts"
            " WHERE %s = ? AND ok = 1 AND at >= ?" % column,
            (value, window_start),
        ).fetchone()[0]
        floor = max(window_start, last_success) if last_success else window_start
        failures = conn.execute(
            "SELECT COUNT(*) FROM login_attempts"
            " WHERE %s = ? AND ok = 0 AND at > ?" % column,
            (value, floor),
        ).fetchone()[0]
        if failures >= LOCKOUT_THRESHOLD:
            return True
    return False


def list_attempts(
    conn: sqlite3.Connection, limit: int = 100, offset: int = 0
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT email, ip, user_agent, ok, at FROM login_attempts"
        " ORDER BY at DESC, id DESC LIMIT ? OFFSET ?",
        (max(1, min(limit, 500)), max(0, offset)),
    ).fetchall()
    return [
        {"email": r["email"], "ip": r["ip"], "user_agent": r["user_agent"],
         "ok": bool(r["ok"]), "at": r["at"]}
        for r in rows
    ]


# -- bootstrap --------------------------------------------------------------

def bootstrap_admin(conn: sqlite3.Connection) -> dict[str, Any] | None:
    """Sem nenhum admin ativo no banco, cria o primeiro a partir do ambiente.

    A senha vem de variável de ambiente — visível em `docker inspect`, no
    histórico de shell e no compose — então a conta nasce com troca
    obrigatória: serve para entrar uma vez, não para ser a senha real.
    """
    if count_active_admins(conn) > 0:
        return None
    email = os.environ.get("ARBITES_ADMIN_EMAIL", "").strip()
    password = os.environ.get("ARBITES_ADMIN_PASSWORD", "")
    if not email or not password:
        return None
    existing = get_user_by_email(conn, email)
    if existing is not None:
        conn.execute(
            "UPDATE users SET role = 'admin', status = 'active' WHERE id = ?",
            (existing["id"],),
        )
        conn.commit()
        return get_user(conn, existing["id"])
    try:
        validate_password(password)
    except AuthError:
        return None
    return create_user(
        conn, email, password, name="Administrador", role="admin",
        status="active", must_change_password=True,
    )


def authenticate(
    conn: sqlite3.Connection, email: str, password: str, ip: str = "",
    user_agent: str = "",
) -> dict[str, Any]:
    """Valida credencial e devolve o usuário, ou levanta AuthError.

    Toda recusa que não seja lockout usa a MESMA resposta: conta
    inexistente, pendente, desativada, recusada e senha errada são
    indistinguíveis de fora.
    """
    email = (email or "").strip()
    if is_locked_out(conn, email, ip):
        record_attempt(conn, email, ip, False, user_agent)
        raise AuthError(
            429, "locked_out", "muitas tentativas; tente de novo em alguns minutos",
        )
    row = get_user_by_email(conn, email)
    ok = verify_password(row["password_hash"] if row else None, password)
    if not ok or row["status"] != "active":
        record_attempt(conn, email, ip, False, user_agent)
        raise AuthError(401, "invalid_credentials", "e-mail ou senha inválidos")
    record_attempt(conn, email, ip, True, user_agent)
    return _row_to_user(row)


# -- credencial do agente (MCP, change 0146) --------------------------------
#
# SEPARADA da sessão do navegador de propósito: revogar o acesso do agente
# não pode derrubar a sua sessão, e a recíproca também vale. Ela HERDA o
# papel da conta que a gerou — o agente nunca alcança mais que a pessoa — e
# não expira por inatividade, porque um agente pode ficar dias sem chamar e
# continuar sendo o mesmo agente.
#
# Guardamos o HASH, como na sessão: quem tem o banco não tem o token.

AGENT_TOKEN_PREFIX = "arb_"


def create_agent_token(
    conn: sqlite3.Connection, user_id: int, name: str
) -> tuple[str, dict[str, Any]]:
    """Cria e devolve (token em claro, metadados). O claro só existe aqui."""
    if not name.strip():
        raise AuthError(422, "name_required", "dê um nome à credencial")
    raw = AGENT_TOKEN_PREFIX + secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO agent_tokens (token_hash, name, user_id, created_at)"
        " VALUES (?, ?, ?, ?)",
        (_hash_token(raw), name.strip(), user_id, _iso(_now())),
    )
    conn.commit()
    return raw, {"name": name.strip(), "created_at": _iso(_now()), "last_used_at": None}


def list_agent_tokens(conn: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    return [
        {"id": row["token_hash"][:12], "name": row["name"],
         "created_at": row["created_at"], "last_used_at": row["last_used_at"]}
        for row in conn.execute(
            "SELECT token_hash, name, created_at, last_used_at FROM agent_tokens"
            " WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    ]


def revoke_agent_token(conn: sqlite3.Connection, user_id: int, token_id: str) -> bool:
    """Revoga pelo prefixo do hash — o valor em claro ninguém mais tem."""
    cur = conn.execute(
        "DELETE FROM agent_tokens WHERE user_id = ? AND token_hash LIKE ?",
        (user_id, token_id + "%"),
    )
    conn.commit()
    return cur.rowcount > 0


def resolve_agent_token(
    conn: sqlite3.Connection, raw: str | None
) -> dict[str, Any] | None:
    """Valida a credencial do agente e devolve o usuário dono, ou None.

    Sem expiração por inatividade (ver acima), mas conta que deixou de estar
    ativa derruba a credencial junto: o agente não sobrevive à pessoa."""
    if not raw or not raw.startswith(AGENT_TOKEN_PREFIX):
        return None
    token_hash = _hash_token(raw)
    row = conn.execute(
        "SELECT user_id FROM agent_tokens WHERE token_hash = ?", (token_hash,)
    ).fetchone()
    if row is None:
        return None
    user = get_user(conn, row["user_id"])
    if user is None or user["status"] != "active":
        conn.execute("DELETE FROM agent_tokens WHERE token_hash = ?", (token_hash,))
        conn.commit()
        return None
    conn.execute(
        "UPDATE agent_tokens SET last_used_at = ? WHERE token_hash = ?",
        (_iso(_now()), token_hash),
    )
    conn.commit()
    return user


# -- interruptores de superfície --------------------------------------------

# Cada entrada governa uma CAPACIDADE, não uma URL: quando uma rota nova faz
# a mesma coisa, ela entra no interruptor existente em vez de escapar dele.
SWITCHES: dict[str, str] = {
    "local_runner": "Execução local de automação (subprocess no servidor)",
    "filesystem_browse": "Navegação do filesystem do servidor",
    "target_env": "Leitura e escrita do .env dos projetos-alvo",
    "ai": "Chamadas aos providers de IA",
    "xray_import": "Importação de XML do Xray",
}

# MÓDULOS do produto (ADR 0014). Um módulo é uma TELA mais os caminhos de API
# que só ela usa — outra pergunta da que os interruptores acima respondem:
# aqueles governam uma CAPACIDADE técnica (rodar subprocess, ler o .env),
# estes governam se a feature existe nesta instância.
#
# Desligado, o módulo some do menu, recusa o deep link e responde 403 em
# todos os seus caminhos. Ausente no banco = ligado, para não mudar o
# comportamento de quem já instalou.
#
# O núcleo NÃO entra aqui: requisitos, test cases, execuções, dashboard,
# defeitos, afazeres, auditoria, problemas, perfil e a própria administração
# não são desligáveis — sem eles não sobra produto, e um interruptor que
# permite se trancar para fora do painel é uma armadilha.
MODULES: dict[str, dict[str, Any]] = {
    "mod_ia": {
        "label": "Assistente de IA",
        # o Context Pack mora nesta tela e vai junto (ADR 0014, consequência
        # negativa declarada): o módulo é a tela, não o botão
        "tab": "ia",
        "paths": ("/ai", "/context-pack", "/agent-pack"),
    },
    "mod_automation": {
        "label": "Automação",
        "tab": "automation",
        "paths": ("/targets", "/automation", "/runs", "/env"),
    },
    "mod_migration": {
        "label": "Migração do Xray",
        "tab": "migration",
        "paths": ("/import/xray",),
    },
    "mod_decisions": {
        "label": "Decisões",
        "tab": "decisions",
        "paths": ("/decisions",),
    },
    "mod_memory": {
        "label": "Memória do projeto",
        "tab": "memory",
        "paths": ("/memory",),
    },
    "mod_daily": {
        "label": "Daily",
        "tab": "daily",
        "paths": ("/daily", "/dailies"),
    },
    "mod_meetings": {
        "label": "Reuniões",
        "tab": "meetings",
        "paths": ("/meetings",),
    },
}


def _all_switch_labels() -> dict[str, tuple[str, str, str | None]]:
    """name -> (label, kind, tab). Uma só fonte para listar e validar."""
    out: dict[str, tuple[str, str, str | None]] = {
        name: (label, "surface", None) for name, label in SWITCHES.items()
    }
    for name, spec in MODULES.items():
        out[name] = (spec["label"], "module", spec["tab"])
    return out


def list_switches(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Estado de todos os interruptores conhecidos. Ausente no banco = ligado:
    o default preserva o comportamento da instalação local."""
    stored = {
        row["name"]: row
        for row in conn.execute("SELECT * FROM switches").fetchall()
    }
    out = []
    for name, (label, kind, tab) in _all_switch_labels().items():
        row = stored.get(name)
        out.append({
            "name": name,
            "label": label,
            # o cliente agrupa por `kind`: superfície perigosa e módulo do
            # produto respondem a perguntas diferentes (ADR 0014)
            "kind": kind,
            "tab": tab,
            "enabled": bool(row["enabled"]) if row is not None else True,
            "updated_at": row["updated_at"] if row is not None else None,
            "updated_by": row["updated_by"] if row is not None else None,
        })
    return out


def switch_enabled(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT enabled FROM switches WHERE name = ?", (name,)
    ).fetchone()
    return True if row is None else bool(row["enabled"])


def set_switch(
    conn: sqlite3.Connection, name: str, enabled: bool, updated_by: str = ""
) -> dict[str, Any]:
    if name not in _all_switch_labels():
        raise AuthError(404, "unknown_switch", "interruptor inexistente: %s" % name)
    conn.execute(
        "INSERT INTO switches (name, enabled, updated_at, updated_by)"
        " VALUES (?, ?, ?, ?)"
        " ON CONFLICT(name) DO UPDATE SET enabled = excluded.enabled,"
        " updated_at = excluded.updated_at, updated_by = excluded.updated_by",
        (name, int(enabled), _iso(_now()), updated_by),
    )
    conn.commit()
    return next(s for s in list_switches(conn) if s["name"] == name)


# -- log de atividade -------------------------------------------------------
#
# Contínuo e imutável, ao lado das rodadas de auditoria de qualidade. Vive no
# banco durável porque um reindex não pode apagar a prova de quem apagou o
# quê, e não existe rota que o edite ou remova: registro que o próprio
# suspeito apaga não prova nada.


def record_activity(
    conn: sqlite3.Connection,
    user: dict[str, Any] | None,
    method: str,
    path: str,
    status_code: int,
    ip: str = "",
) -> None:
    conn.execute(
        "INSERT INTO activity (at, user_id, user_email, method, path,"
        " status_code, ip) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (_iso(_now()), (user or {}).get("id"), (user or {}).get("email", ""),
         method, path, status_code, ip),
    )
    conn.commit()


def list_activity(
    conn: sqlite3.Connection,
    limit: int = 100,
    offset: int = 0,
    user: str = "",
    path: str = "",
    date_from: str = "",
    date_to: str = "",
) -> list[dict[str, Any]]:
    clauses, params = [], []
    if user:
        clauses.append("user_email = ? COLLATE NOCASE")
        params.append(user.strip())
    if path:
        clauses.append("path LIKE ?")
        params.append("%%%s%%" % path.strip())
    if date_from:
        clauses.append("at >= ?")
        params.append(date_from)
    if date_to:
        # Data solta significa o dia inteiro, não o instante zero dele.
        params.append(date_to if len(date_to) > 10 else date_to + "T23:59:59Z")
        clauses.append("at <= ?")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.extend([max(1, min(limit, 500)), max(0, offset)])
    rows = conn.execute(
        "SELECT at, user_email, method, path, status_code, ip FROM activity"
        + where + " ORDER BY at DESC, id DESC LIMIT ? OFFSET ?",
        params,
    ).fetchall()
    return [
        {"at": r["at"], "user_email": r["user_email"], "method": r["method"],
         "path": r["path"], "status_code": r["status_code"], "ip": r["ip"]}
        for r in rows
    ]
