"""Testes do painel de administração — acceptance criteria do 0102."""

import pytest

from arbites import auth as auth_ops
from conftest import ADMIN_EMAIL

CANDIDATE = {"email": "novato@arbites.test", "password": "senha-do-novato-1",
             "name": "Novato"}


def _conn(test_client):
    return test_client.app.state.auth


def _register(test_client, credentials=CANDIDATE) -> int:
    response = test_client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201
    return response.json()["user"]["id"]


def _find(users, email):
    return next(u for u in users if u["email"] == email)


# -- AC1: fila de pendentes e aprovação com papel numa só ação --------------


def test_cadastro_entra_na_fila_e_aprovacao_ja_define_o_papel(client):
    user_id = _register(client)

    listed = client.get("/api/v1/admin/users").json()["users"]
    candidate = _find(listed, CANDIDATE["email"])
    assert candidate["status"] == "pending"
    assert candidate["open_sessions"] == 0

    approved = client.post(
        f"/api/v1/admin/users/{user_id}/approve", json={"role": "editor"}
    )
    assert approved.status_code == 200
    assert approved.json()["user"]["status"] == "active"
    assert approved.json()["user"]["role"] == "editor"

    # A conta entra já como editor: sem janela em que ela loga com o papel
    # errado esperando uma segunda ação.
    login = client.post("/api/v1/auth/login", json={
        "email": CANDIDATE["email"], "password": CANDIDATE["password"]})
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "editor"


def test_recusar_um_cadastro_impede_o_login(client):
    user_id = _register(client)
    assert client.post(f"/api/v1/admin/users/{user_id}/reject").status_code == 200
    refused = client.post("/api/v1/auth/login", json={
        "email": CANDIDATE["email"], "password": CANDIDATE["password"]})
    assert refused.status_code == 401


# -- AC2: desativar encerra sessões -----------------------------------------


def test_desativar_encerra_as_sessoes_e_reativar_nao_as_devolve(client):
    user_id = _register(client)
    client.post(f"/api/v1/admin/users/{user_id}/approve", json={"role": "viewer"})
    auth_ops.open_session(_conn(client), user_id, "10.0.0.5", "navegador")

    listed = _find(client.get("/api/v1/admin/users").json()["users"],
                   CANDIDATE["email"])
    assert listed["open_sessions"] == 1

    client.post(f"/api/v1/admin/users/{user_id}/disable")
    listed = _find(client.get("/api/v1/admin/users").json()["users"],
                   CANDIDATE["email"])
    assert listed["status"] == "disabled"
    assert listed["open_sessions"] == 0

    client.post(f"/api/v1/admin/users/{user_id}/enable")
    listed = _find(client.get("/api/v1/admin/users").json()["users"],
                   CANDIDATE["email"])
    assert listed["status"] == "active"
    assert listed["open_sessions"] == 0


def test_encerrar_sessoes_nao_altera_o_status_da_conta(client):
    user_id = _register(client)
    client.post(f"/api/v1/admin/users/{user_id}/approve", json={"role": "viewer"})
    auth_ops.open_session(_conn(client), user_id, "10.0.0.5", "navegador")

    revoked = client.delete(f"/api/v1/admin/users/{user_id}/sessions")
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] == 1
    # Barrar quem quer entrar é outra decisão: a conta continua ativa.
    assert revoked.json()["user"]["status"] == "active"


# -- AC3: senha temporária ---------------------------------------------------


def test_senha_temporaria_derruba_sessoes_e_obriga_troca(anon_client):
    from conftest import login_admin
    login_admin(anon_client)
    user_id = _register(anon_client)
    anon_client.post(f"/api/v1/admin/users/{user_id}/approve",
                     json={"role": "editor"})
    auth_ops.open_session(_conn(anon_client), user_id, "10.0.0.5", "x")

    reset = anon_client.post(
        f"/api/v1/admin/users/{user_id}/password",
        json={"password": "temporaria-do-admin-1"},
    )
    assert reset.status_code == 200
    assert reset.json()["user"]["must_change_password"] is True
    assert auth_ops.count_sessions(_conn(anon_client), user_id) == 0

    # A senha antiga morreu; a temporária entra mas não deixa trabalhar.
    assert anon_client.post("/api/v1/auth/login", json={
        "email": CANDIDATE["email"],
        "password": CANDIDATE["password"]}).status_code == 401
    assert anon_client.post("/api/v1/auth/login", json={
        "email": CANDIDATE["email"],
        "password": "temporaria-do-admin-1"}).status_code == 200
    blocked = anon_client.get("/api/v1/workspace")
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "password_change_required"


def test_nenhuma_resposta_do_painel_vaza_hash_ou_sessao(client):
    user_id = _register(client)
    bodies = [
        client.get("/api/v1/admin/users").text,
        client.post(f"/api/v1/admin/users/{user_id}/approve",
                    json={"role": "viewer"}).text,
        client.post(f"/api/v1/admin/users/{user_id}/password",
                    json={"password": "temporaria-do-admin-1"}).text,
        client.get("/api/v1/admin/access-log").text,
    ]
    for body in bodies:
        assert "$argon2" not in body
        assert "password_hash" not in body
        assert "token_hash" not in body


# -- AC4: log de acesso ------------------------------------------------------


def test_log_de_acesso_lista_sucesso_e_falha_mais_recente_primeiro(client):
    client.post("/api/v1/auth/login",
                json={"email": "fantasma@arbites.test", "password": "errada-longa-1"},
                headers={"CF-Connecting-IP": "203.0.113.7"})

    attempts = client.get("/api/v1/admin/access-log").json()["attempts"]
    assert attempts[0]["email"] == "fantasma@arbites.test"
    assert attempts[0]["ok"] is False
    assert attempts[0]["ip"] == "203.0.113.7"
    # O login do admin, feito pela fixture, continua no registro.
    assert any(a["email"] == ADMIN_EMAIL and a["ok"] for a in attempts)
    assert [a["at"] for a in attempts] == sorted(
        (a["at"] for a in attempts), reverse=True)


def test_log_de_acesso_pagina(client):
    for i in range(6):
        client.post("/api/v1/auth/login",
                    json={"email": f"n{i}@arbites.test", "password": "errada-longa-1"})
    first = client.get("/api/v1/admin/access-log?limit=3").json()["attempts"]
    second = client.get("/api/v1/admin/access-log?limit=3&offset=3").json()["attempts"]
    assert len(first) == len(second) == 3
    assert {a["at"] for a in first}.isdisjoint({a["at"] for a in second})


# -- AC5: o painel inteiro é privativo do admin ------------------------------


def test_nenhuma_rota_do_painel_responde_a_papel_menor(anon_client):
    auth_ops.create_user(_conn(anon_client), "editor2@arbites.test",
                         "senha-de-editor-1", role="editor", status="active")
    anon_client.post("/api/v1/auth/login", json={
        "email": "editor2@arbites.test", "password": "senha-de-editor-1"})

    checked = 0
    for route in anon_client.app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/v1/admin/"):
            continue
        for method in sorted(getattr(route, "methods", set()) or set()):
            if method in {"HEAD", "OPTIONS"}:
                continue
            concrete = path.replace("{user_id}", "1").replace("{name}", "ai")
            if method == "GET" and concrete == "/api/v1/admin/switches":
                continue  # exceção deliberada: a UI precisa saber o que esconder
            response = anon_client.request(method, concrete, json={})
            assert response.status_code == 403, "%s %s" % (method, concrete)
            assert response.json()["error"]["code"] == "forbidden"
            checked += 1
    assert checked >= 9, "a varredura cobriu apenas %d rotas" % checked


def test_o_painel_nao_oferece_exclusao_de_conta(client):
    """Desativar preserva a autoria histórica; apagar reescreveria o passado."""
    deleting = [
        (m, getattr(r, "path", ""))
        for r in client.app.routes
        for m in (getattr(r, "methods", set()) or set())
        if m == "DELETE" and getattr(r, "path", "").startswith("/api/v1/admin/users")
    ]
    # A única rota DELETE do painel encerra sessões, não apaga a conta.
    assert deleting == [("DELETE", "/api/v1/admin/users/{user_id}/sessions")]


# -- AC6: o admin não se derruba, e o último admin é intocável ---------------


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [("POST", "disable", None), ("POST", "reject", None),
     ("PUT", "role", {"role": "viewer"})],
)
def test_admin_nao_altera_a_si_mesmo(client, method, suffix, body):
    me = client.get("/api/v1/auth/me").json()["user"]
    response = client.request(
        method, f"/api/v1/admin/users/{me['id']}/{suffix}", json=body or {})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "self_demotion"


def test_ultimo_admin_ativo_e_intocavel_pelo_painel(client):
    """Com dois admins, rebaixar um é possível; o que sobra, não."""
    conn = _conn(client)
    second = auth_ops.create_user(conn, "admin2@arbites.test",
                                  "segunda-senha-admin-1", role="admin",
                                  status="active")
    demoted = client.put(f"/api/v1/admin/users/{second['id']}/role",
                         json={"role": "viewer"})
    assert demoted.status_code == 200

    # Agora só resta um admin ativo — e ele é o próprio requisitante, então a
    # trava de auto-alteração responde antes da do último admin.
    me = client.get("/api/v1/auth/me").json()["user"]
    assert client.post(
        f"/api/v1/admin/users/{me['id']}/disable"
    ).json()["error"]["code"] == "self_demotion"

    # Pela via direta, a trava do último admin também recusa.
    with pytest.raises(auth_ops.AuthError) as raised:
        auth_ops.set_status(conn, me["id"], "disabled")
    assert raised.value.code == "last_admin"


# -- AC7: retrato operacional ------------------------------------------------


def test_overview_traz_contas_indice_lixeira_e_versao(client):
    _register(client)
    overview = client.get("/api/v1/admin/overview").json()
    assert overview["users"]["pending"] == 1
    assert overview["users"]["active"] >= 1
    assert overview["index"]["last_reindex"] is not None
    assert overview["trash_items"] == 0
    assert overview["version"]
    assert len(overview["switches"]) == len(auth_ops.SWITCHES) + len(
        auth_ops.MODULES
    )


def test_overview_conta_a_lixeira(client):
    created = client.post("/api/v1/testcases", json={"title": "Descartável"}).json()
    client.delete(f"/api/v1/testcases/{created['id']}")
    assert client.get("/api/v1/admin/overview").json()["trash_items"] == 1
