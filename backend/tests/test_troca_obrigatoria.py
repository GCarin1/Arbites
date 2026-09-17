"""O contrato que a tela de troca obrigatória consome (change 0169).

A SPA precisa de duas coisas para levar alguém à troca de senha em vez de
montar o app e tomar 403 em tudo: o usuário devolvido pelo login precisa
dizer que a troca é devida, e a recusa das demais rotas precisa vir com um
código estável — não só um 403 genérico, indistinguível de falta de papel.
"""

import pytest
from conftest import ADMIN_EMAIL, BOOTSTRAP_PASSWORD, ADMIN_PASSWORD
from fastapi.testclient import TestClient

from arbites.api import create_app


@pytest.fixture()
def devendo_troca(ws):
    """Cliente logado numa conta que ainda deve a troca de senha."""
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.ws = ws
        r = client.post("/api/v1/auth/login", json={
            "email": ADMIN_EMAIL, "password": BOOTSTRAP_PASSWORD})
        assert r.status_code == 200, r.text
        client.login = r.json()
        yield client


def test_o_login_avisa_que_a_troca_e_devida(devendo_troca):
    """Sem este campo a tela não tem como saber para onde mandar a pessoa."""
    assert devendo_troca.login["user"]["must_change_password"] is True


def test_me_repete_o_aviso_para_quem_recarrega_a_pagina(devendo_troca):
    corpo = devendo_troca.get("/api/v1/auth/me").json()
    assert corpo["user"]["must_change_password"] is True


def test_a_recusa_tem_codigo_proprio_e_nao_um_403_qualquer(devendo_troca):
    """`password_change_required` é o que a SPA usa para voltar à troca.

    Um 403 sem código seria indistinguível de "papel não alcança a rota", e
    a tela não teria como reagir — foi assim que a sessão ficou presa
    pedindo dados que nunca chegavam.
    """
    r = devendo_troca.get("/api/v1/workspace")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "password_change_required"


def test_as_tres_rotas_de_saida_continuam_abertas(devendo_troca):
    """Trocar, olhar quem sou e sair: sem elas não há como escapar."""
    assert devendo_troca.get("/api/v1/auth/me").status_code == 200
    r = devendo_troca.post("/api/v1/auth/password", json={
        "current_password": BOOTSTRAP_PASSWORD, "new_password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    # E a obrigação sai junto — a sessão rotacionada já alcança o app.
    assert r.json()["user"]["must_change_password"] is False
    assert devendo_troca.get("/api/v1/workspace").status_code == 200


def test_trocar_a_senha_pelo_perfil_usa_a_mesma_rota(ws):
    """O cartão Senha do Perfil não é uma rota nova: é `POST /auth/password`
    com a sessão já dentro do app, sem obrigação pendente."""
    from conftest import logged_in_client

    with logged_in_client(ws) as client:
        r = client.post("/api/v1/auth/password", json={
            "current_password": ADMIN_PASSWORD,
            "new_password": "senha-escolhida-no-perfil-1"})
        assert r.status_code == 200, r.text
        assert r.json()["user"]["must_change_password"] is False
        # A sessão de quem trocou continua valendo (ela é rotacionada).
        assert client.get("/api/v1/workspace").status_code == 200
