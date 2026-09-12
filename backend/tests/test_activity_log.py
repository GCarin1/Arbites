"""Testes do log central de atividade — acceptance criteria do 0103."""

from arbites import auth as auth_ops
from conftest import ADMIN_EMAIL


def _entries(test_client, query=""):
    return test_client.get("/api/v1/admin/activity" + query).json()["entries"]


# -- AC1: escrita bem-sucedida vira entrada com autor, método, caminho e IP --


def test_criar_editar_e_apagar_deixam_tres_entradas(client):
    created = client.post(
        "/api/v1/testcases", json={"title": "Login válido"},
        headers={"CF-Connecting-IP": "203.0.113.7"},
    ).json()
    client.put(f"/api/v1/testcases/{created['id']}",
               json={"title": "Login válido (revisado)"},
               headers={"CF-Connecting-IP": "203.0.113.7"})
    client.delete(f"/api/v1/testcases/{created['id']}",
                  headers={"CF-Connecting-IP": "203.0.113.7"})

    entries = _entries(client, "?path=/testcases")
    assert [e["method"] for e in entries] == ["DELETE", "PUT", "POST"]
    assert all(e["user_email"] == ADMIN_EMAIL for e in entries)
    assert all(e["ip"] == "203.0.113.7" for e in entries)
    assert entries[-1]["path"] == "/api/v1/testcases"
    assert entries[0]["path"].endswith(created["id"])


def test_uma_rota_de_escrita_nao_anotada_a_mao_tambem_entra(client):
    """O registro mora no gate: nada precisa ser anotado por rota."""
    client.post("/api/v1/workspace/reindex")
    assert any(
        e["path"] == "/api/v1/workspace/reindex" and e["method"] == "POST"
        for e in _entries(client)
    )


# -- AC2: recusa e leitura ficam de fora -------------------------------------


def test_escrita_recusada_por_papel_nao_entra_no_log(anon_client):
    from conftest import login_admin

    conn = anon_client.app.state.auth
    auth_ops.create_user(conn, "viewer3@arbites.test", "senha-de-viewer-1",
                         role="viewer", status="active")
    anon_client.post("/api/v1/auth/login", json={
        "email": "viewer3@arbites.test", "password": "senha-de-viewer-1"})
    refused = anon_client.post("/api/v1/testcases", json={"title": "Não deve entrar"})
    assert refused.status_code == 403

    anon_client.post("/api/v1/auth/logout")
    login_admin(anon_client)
    assert not any(
        e["user_email"] == "viewer3@arbites.test" for e in _entries(anon_client)
    )


def test_escrita_recusada_por_interruptor_nao_entra_no_log(client):
    client.put("/api/v1/admin/switches/local_runner", json={"enabled": False})
    refused = client.post("/api/v1/runs/local",
                          json={"target": "x", "testcase_ids": ["CT-1"]})
    assert refused.status_code == 403
    assert not any(e["path"] == "/api/v1/runs/local" for e in _entries(client))


def test_leitura_por_get_nao_entra_no_log(client):
    client.get("/api/v1/testcases")
    client.get("/api/v1/requirements")
    assert all(e["method"] != "GET" for e in _entries(client))


def test_autenticacao_fica_no_registro_de_acessos_e_nao_aqui(anon_client):
    from conftest import login_admin

    login_admin(anon_client)
    paths = {e["path"] for e in _entries(anon_client)}
    assert not any(p.startswith("/api/v1/auth/") for p in paths)
    # Mas o login está registrado — no lugar dele.
    assert anon_client.get("/api/v1/admin/access-log").json()["attempts"]


# -- AC3: filtros e paginação ------------------------------------------------


def test_filtra_por_autor_por_caminho_e_pagina(anon_client):
    from conftest import login_admin

    conn = anon_client.app.state.auth
    auth_ops.create_user(conn, "editor3@arbites.test", "senha-de-editor-1",
                         role="editor", status="active")
    anon_client.post("/api/v1/auth/login", json={
        "email": "editor3@arbites.test", "password": "senha-de-editor-1"})
    for i in range(3):
        anon_client.post("/api/v1/testcases", json={"title": f"CT do editor {i}"})
    anon_client.post("/api/v1/auth/logout")

    login_admin(anon_client)
    anon_client.post("/api/v1/requirements", json={"kind": "epic", "title": "Épico"})

    by_author = _entries(anon_client, "?user=editor3@arbites.test")
    assert len(by_author) == 3
    assert all(e["user_email"] == "editor3@arbites.test" for e in by_author)

    by_path = _entries(anon_client, "?path=/requirements")
    assert len(by_path) == 1
    assert by_path[0]["user_email"] == ADMIN_EMAIL

    page = _entries(anon_client, "?limit=2")
    rest = _entries(anon_client, "?limit=2&offset=2")
    assert len(page) == 2 and len(rest) == 2
    assert {e["at"] for e in page}.isdisjoint({e["at"] for e in rest})


def test_filtra_por_intervalo_de_datas(client):
    client.post("/api/v1/testcases", json={"title": "De hoje"})
    hoje = _entries(client)[0]["at"][:10]

    assert _entries(client, f"?date_from={hoje}")
    assert _entries(client, f"?date_to={hoje}")
    assert _entries(client, "?date_from=2099-01-01") == []
    assert _entries(client, "?date_to=2000-01-01") == []


# -- AC4: sem corpo, sem exclusão, imune ao reindex --------------------------


def test_o_log_nao_guarda_corpo_de_requisicao(client):
    client.post("/api/v1/testcases", json={"title": "Segredo no título"})
    raw = client.get("/api/v1/admin/activity").text
    assert "Segredo no título" not in raw
    entry = _entries(client)[0]
    assert set(entry) == {"at", "user_email", "method", "path", "status_code", "ip"}


def test_nao_existe_rota_que_apague_ou_edite_o_log(client):
    """Registro que o próprio suspeito apaga não prova nada."""
    mutating = [
        (method, getattr(route, "path", ""))
        for route in client.app.routes
        for method in (getattr(route, "methods", set()) or set())
        if getattr(route, "path", "").startswith("/api/v1/admin/activity")
        and method not in {"GET", "HEAD", "OPTIONS"}
    ]
    assert mutating == []


def test_reindexar_o_workspace_nao_afeta_o_log(client, ws):
    from arbites.indexer import connect, reindex_full

    client.post("/api/v1/testcases", json={"title": "Antes do reindex"})
    before = len(_entries(client))
    assert before >= 1

    index_conn = connect(ws)
    reindex_full(ws, index_conn)
    index_conn.close()

    assert len(_entries(client)) == before


def test_o_log_e_admin_only(anon_client):
    conn = anon_client.app.state.auth
    auth_ops.create_user(conn, "editor4@arbites.test", "senha-de-editor-1",
                         role="editor", status="active")
    anon_client.post("/api/v1/auth/login", json={
        "email": "editor4@arbites.test", "password": "senha-de-editor-1"})
    response = anon_client.get("/api/v1/admin/activity")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
