"""Testes da capability `auth` — um bloco por acceptance criterion da spec."""

import sqlite3

import pytest

from arbites import auth as auth_ops
from conftest import ADMIN_EMAIL, ADMIN_PASSWORD, BOOTSTRAP_PASSWORD, login_admin

NEW_USER = {"email": "qa@arbites.test", "password": "senha-de-qa-longa-1",
            "name": "QA"}


def _auth_conn(test_client) -> sqlite3.Connection:
    return test_client.app.state.auth


# -- AC1: cadastro nasce pendente e nao autentica ---------------------------


def test_cadastro_nasce_pendente_e_nao_loga_ate_aprovacao(anon_client):
    created = anon_client.post("/api/v1/auth/register", json=NEW_USER)
    assert created.status_code == 201
    assert created.json()["user"]["status"] == "pending"
    assert created.json()["user"]["role"] == "viewer"
    # Cadastrar nao abre sessao.
    assert auth_ops.SESSION_COOKIE not in anon_client.cookies

    refused = anon_client.post(
        "/api/v1/auth/login",
        json={"email": NEW_USER["email"], "password": NEW_USER["password"]},
    )
    assert refused.status_code == 401
    assert refused.json()["error"]["code"] == "invalid_credentials"

    # Aprovado, o mesmo login passa.
    conn = _auth_conn(anon_client)
    user = auth_ops.get_user_by_email(conn, NEW_USER["email"])
    auth_ops.set_status(conn, user["id"], "active")
    accepted = anon_client.post(
        "/api/v1/auth/login",
        json={"email": NEW_USER["email"], "password": NEW_USER["password"]},
    )
    assert accepted.status_code == 200


def test_cadastro_recusa_senha_curta_e_email_repetido(anon_client):
    weak = anon_client.post(
        "/api/v1/auth/register", json={"email": "x@y.com", "password": "curta"}
    )
    assert weak.status_code == 422
    assert weak.json()["error"]["code"] == "weak_password"

    anon_client.post("/api/v1/auth/register", json=NEW_USER)
    duplicate = anon_client.post("/api/v1/auth/register", json=NEW_USER)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "email_taken"


def test_signup_off_recusa_cadastro(anon_client, monkeypatch):
    monkeypatch.setenv("ARBITES_SIGNUP", "off")
    response = anon_client.post("/api/v1/auth/register", json=NEW_USER)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "signup_disabled"


# -- AC2: cookie httpOnly + SameSite=Lax, sem dados do usuario --------------


def test_login_emite_cookie_httponly_opaco(anon_client):
    response = anon_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": BOOTSTRAP_PASSWORD},
    )
    assert response.status_code == 200

    raw = response.headers["set-cookie"].lower()
    assert "httponly" in raw
    assert "samesite=lax" in raw
    assert "path=/" in raw

    token = anon_client.cookies[auth_ops.SESSION_COOKIE]
    # O cookie carrega um identificador opaco: nada do usuario vaza nele.
    assert ADMIN_EMAIL not in token
    assert "admin" not in token.lower()
    assert len(token) >= 40

    # E o banco guarda so o hash do token, nunca o token.
    stored = _auth_conn(anon_client).execute(
        "SELECT token_hash FROM sessions"
    ).fetchall()
    assert len(stored) == 1
    assert stored[0]["token_hash"] != token

    me = anon_client.get("/api/v1/auth/me")
    assert me.json()["user"]["email"] == ADMIN_EMAIL


# -- AC3: gate 401 em toda a API, com allowlist -----------------------------


@pytest.mark.parametrize(
    "path",
    ["/api/v1/workspace", "/api/v1/requirements", "/api/v1/testcases",
     "/api/v1/executions", "/api/v1/metrics/summary", "/api/v1/trash"],
)
def test_sem_sessao_toda_rota_da_api_responde_401(anon_client, path):
    response = anon_client.get(path)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_rotas_publicas_respondem_sem_sessao(anon_client):
    assert anon_client.get("/api/v1/health").status_code == 200
    # /auth/me sem sessao responde 200 com user nulo — a SPA usa isso para
    # decidir entre a tela de login e a aplicacao.
    me = anon_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"] is None
    assert anon_client.post(
        "/api/v1/auth/login", json={"email": "x@y.com", "password": "zzz"}
    ).status_code == 401


def test_cookie_desconhecido_e_401_e_apaga_o_cookie(anon_client):
    anon_client.cookies.set(auth_ops.SESSION_COOKIE, "token-que-nunca-existiu")
    response = anon_client.get("/api/v1/workspace")
    assert response.status_code == 401
    assert 'arbites_session=""' in response.headers.get("set-cookie", "") \
        or "arbites_session=;" in response.headers.get("set-cookie", "")


def test_auth_off_libera_a_api(ws, monkeypatch):
    from fastapi.testclient import TestClient

    from arbites.api import create_app

    monkeypatch.setenv("ARBITES_AUTH", "off")
    with TestClient(create_app(ws.root, watch=False)) as test_client:
        assert test_client.get("/api/v1/workspace").status_code == 200
        assert test_client.get("/api/v1/auth/me").json()["auth_enabled"] is False


# -- AC4: lockout e resposta indistinguivel ---------------------------------


def test_cinco_falhas_travam_a_conta_por_quinze_minutos(anon_client):
    for _ in range(auth_ops.LOCKOUT_THRESHOLD):
        failed = anon_client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": "senha-errada-1"},
        )
        assert failed.status_code == 401

    locked = anon_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "senha-errada-1"},
    )
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "locked_out"

    # Travou de verdade: nem a senha certa passa durante a janela.
    correct = anon_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": BOOTSTRAP_PASSWORD},
    )
    assert correct.status_code == 429


def test_conta_inexistente_e_senha_errada_sao_indistinguiveis(anon_client):
    wrong_password = anon_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "senha-errada-1"},
    )
    unknown_email = anon_client.post(
        "/api/v1/auth/login",
        json={"email": "ninguem@arbites.test", "password": "senha-errada-1"},
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_conta_pendente_responde_igual_a_senha_errada(anon_client):
    anon_client.post("/api/v1/auth/register", json=NEW_USER)
    pending = anon_client.post(
        "/api/v1/auth/login",
        json={"email": NEW_USER["email"], "password": NEW_USER["password"]},
    )
    wrong = anon_client.post(
        "/api/v1/auth/login",
        json={"email": NEW_USER["email"], "password": "outra-senha-longa-1"},
    )
    assert pending.json() == wrong.json()


def test_toda_tentativa_fica_registrada(anon_client):
    anon_client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "errada-longa-1"}
    )
    anon_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": BOOTSTRAP_PASSWORD},
    )
    attempts = auth_ops.list_attempts(_auth_conn(anon_client))
    assert [a["ok"] for a in attempts] == [True, False]
    assert all(a["email"] == ADMIN_EMAIL for a in attempts)


def test_ip_real_vem_do_header_do_tunel(anon_client):
    anon_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "errada-longa-1"},
        headers={"CF-Connecting-IP": "203.0.113.7",
                 "X-Forwarded-For": "198.51.100.9"},
    )
    attempt = auth_ops.list_attempts(_auth_conn(anon_client))[0]
    assert attempt["ip"] == "203.0.113.7"


# -- AC5: mudanca de estado derruba sessao ----------------------------------


def test_desativar_a_conta_derruba_a_sessao_aberta(anon_client):
    login_admin(anon_client)
    assert anon_client.get("/api/v1/workspace").status_code == 200

    conn = _auth_conn(anon_client)
    # Precisa de um segundo admin: o ultimo admin ativo nao pode cair.
    other = auth_ops.create_user(
        conn, "outro@arbites.test", "outra-senha-longa-1", role="admin",
        status="active",
    )
    admin = auth_ops.get_user_by_email(conn, ADMIN_EMAIL)
    auth_ops.set_status(conn, admin["id"], "disabled")

    assert anon_client.get("/api/v1/workspace").status_code == 401
    assert auth_ops.count_sessions(conn, admin["id"]) == 0
    assert other["role"] == "admin"


def test_trocar_o_papel_derruba_a_sessao(anon_client):
    login_admin(anon_client)
    conn = _auth_conn(anon_client)
    auth_ops.create_user(
        conn, "outro@arbites.test", "outra-senha-longa-1", role="admin",
        status="active",
    )
    admin = auth_ops.get_user_by_email(conn, ADMIN_EMAIL)
    auth_ops.set_role(conn, admin["id"], "viewer")
    assert anon_client.get("/api/v1/workspace").status_code == 401


def test_trocar_a_senha_derruba_as_outras_sessoes_e_rotaciona_a_propria(anon_client):
    login_admin(anon_client)
    conn = _auth_conn(anon_client)
    admin = auth_ops.get_user_by_email(conn, ADMIN_EMAIL)
    # Uma segunda sessao da mesma conta, como se fosse outro navegador.
    auth_ops.open_session(conn, admin["id"], "10.0.0.9", "outro-navegador")
    assert auth_ops.count_sessions(conn, admin["id"]) == 2

    before = anon_client.cookies[auth_ops.SESSION_COOKIE]
    changed = anon_client.post(
        "/api/v1/auth/password",
        json={"current_password": ADMIN_PASSWORD,
              "new_password": "terceira-senha-longa-1"},
    )
    assert changed.status_code == 200

    # Sobrou exatamente uma sessao — a rotacionada — e ela nao e a antiga.
    assert auth_ops.count_sessions(conn, admin["id"]) == 1
    assert anon_client.cookies[auth_ops.SESSION_COOKIE] != before
    assert anon_client.get("/api/v1/workspace").status_code == 200


def test_senha_atual_errada_nao_troca_a_senha(anon_client):
    login_admin(anon_client)
    response = anon_client.post(
        "/api/v1/auth/password",
        json={"current_password": "chute-longo-errado-1",
              "new_password": "nova-senha-longa-1"},
    )
    assert response.status_code == 401
    assert anon_client.get("/api/v1/workspace").status_code == 200


def test_ultimo_admin_ativo_nao_pode_cair(anon_client):
    conn = _auth_conn(anon_client)
    admin = auth_ops.get_user_by_email(conn, ADMIN_EMAIL)
    with pytest.raises(auth_ops.AuthError) as disabled:
        auth_ops.set_status(conn, admin["id"], "disabled")
    assert disabled.value.code == "last_admin"
    with pytest.raises(auth_ops.AuthError) as demoted:
        auth_ops.set_role(conn, admin["id"], "viewer")
    assert demoted.value.code == "last_admin"


# -- AC6: bootstrap do admin por ambiente -----------------------------------


def test_bootstrap_cria_o_admin_e_exige_troca_de_senha(anon_client):
    conn = _auth_conn(anon_client)
    admin = auth_ops.get_user_by_email(conn, ADMIN_EMAIL)
    assert admin is not None
    assert admin["role"] == "admin"
    assert admin["status"] == "active"
    assert bool(admin["must_change_password"]) is True

    anon_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": BOOTSTRAP_PASSWORD},
    )
    blocked = anon_client.get("/api/v1/workspace")
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "password_change_required"

    anon_client.post(
        "/api/v1/auth/password",
        json={"current_password": BOOTSTRAP_PASSWORD,
              "new_password": ADMIN_PASSWORD},
    )
    assert anon_client.get("/api/v1/workspace").status_code == 200


def test_bootstrap_nao_roda_quando_ja_existe_admin(ws, monkeypatch):
    conn = auth_ops.connect_auth(ws)
    auth_ops.create_user(
        conn, "primeiro@arbites.test", "primeira-senha-longa-1", role="admin",
        status="active",
    )
    monkeypatch.setenv("ARBITES_ADMIN_EMAIL", "segundo@arbites.test")
    monkeypatch.setenv("ARBITES_ADMIN_PASSWORD", "segunda-senha-longa-1")
    assert auth_ops.bootstrap_admin(conn) is None
    assert auth_ops.get_user_by_email(conn, "segundo@arbites.test") is None


def test_bootstrap_ignora_senha_de_ambiente_fraca(ws, monkeypatch):
    conn = auth_ops.connect_auth(ws)
    monkeypatch.setenv("ARBITES_ADMIN_EMAIL", "fraco@arbites.test")
    monkeypatch.setenv("ARBITES_ADMIN_PASSWORD", "123")
    assert auth_ops.bootstrap_admin(conn) is None


# -- AC7: auth.db sobrevive ao descarte do indice ---------------------------


def test_apagar_o_indice_nao_afeta_contas_nem_sessoes(client, ws):
    from arbites.indexer import connect, reindex_full

    conn = _auth_conn(client)
    admin = auth_ops.get_user_by_email(conn, ADMIN_EMAIL)
    sessions_before = auth_ops.count_sessions(conn, admin["id"])
    assert sessions_before == 1

    # O caminho que a documentacao manda usar quando o indice corrompe.
    index_conn = connect(ws)
    reindex_full(ws, index_conn)
    index_conn.close()

    assert auth_ops.get_user_by_email(conn, ADMIN_EMAIL) is not None
    assert auth_ops.count_sessions(conn, admin["id"]) == sessions_before
    assert client.get("/api/v1/workspace").status_code == 200


def test_contas_ficam_fora_do_workspace_versionavel(client, ws):
    """Nenhum arquivo do workspace pode conter e-mail ou hash de conta."""
    from arbites.auth import auth_db_path

    assert auth_db_path(ws).endswith("auth.db")
    assert ".arbites" in auth_db_path(ws)

    leaked = []
    for path in ws.root.rglob("*"):
        if not path.is_file() or ".arbites" in path.parts:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if ADMIN_EMAIL in content or "$argon2" in content:
            leaked.append(str(path.relative_to(ws.root)))
    assert leaked == []
