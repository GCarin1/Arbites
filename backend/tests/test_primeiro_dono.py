"""Cadastro numa instância sem administrador (change 0168).

Toda conta criada pelo formulário nasce `viewer`/`pending` — alguém precisa
liberar. Quando NÃO existe admin ativo esse alguém não existe, e o pedido
fica pendente para sempre sem que a tela diga nada. Aqui está a prova das
duas saídas: o e-mail que o operador declarou no ambiente vira dono, e
quem não o declarou é avisado antes de se cadastrar.
"""

import pytest
from conftest import ADMIN_EMAIL, BOOTSTRAP_PASSWORD
from fastapi.testclient import TestClient

from arbites.api import create_app

SENHA = "uma-senha-bem-longa-1"


@pytest.fixture()
def sem_admin(ws, monkeypatch):
    """Instância recém-subida: nenhum admin ativo, nenhum e-mail declarado."""
    monkeypatch.delenv("ARBITES_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ARBITES_ADMIN_PASSWORD", raising=False)
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.ws = ws
        yield client


@pytest.fixture()
def dono_declarado(ws, monkeypatch):
    """Instância sem admin, mas com ARBITES_ADMIN_EMAIL declarado.

    Sem a senha: é exatamente o caso de quem põe só o e-mail no `.env` e
    se cadastra pela tela.
    """
    monkeypatch.setenv("ARBITES_ADMIN_EMAIL", "dono@arbites.test")
    monkeypatch.delenv("ARBITES_ADMIN_PASSWORD", raising=False)
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.ws = ws
        yield client


def test_sem_admin_a_tela_avisa_antes_do_cadastro(sem_admin):
    corpo = sem_admin.get("/api/v1/auth/me").json()
    assert corpo["no_admin"] is True
    # Nada declarado: a saída é o comando local, não o formulário.
    assert corpo["owner_declared"] is False


def test_cadastro_comum_continua_pendente_e_sem_privilegio(sem_admin):
    r = sem_admin.post("/api/v1/auth/register", json={
        "email": "qualquer@arbites.test", "password": SENHA, "name": "Fulano"})
    assert r.status_code == 201, r.text
    corpo = r.json()
    # Quem chega primeiro na porta NÃO leva a instância junto.
    assert corpo["admin"] is False
    assert corpo["user"]["role"] == "viewer"
    assert corpo["user"]["status"] == "pending"
    # E continua sem conseguir entrar — pendente responde o mesmo 401.
    entrada = sem_admin.post("/api/v1/auth/login", json={
        "email": "qualquer@arbites.test", "password": SENHA})
    assert entrada.status_code == 401


def test_o_email_declarado_no_ambiente_nasce_admin_ativo(dono_declarado):
    r = dono_declarado.post("/api/v1/auth/register", json={
        "email": "dono@arbites.test", "password": SENHA, "name": "Dono"})
    assert r.status_code == 201, r.text
    corpo = r.json()
    assert corpo["admin"] is True
    assert corpo["user"]["role"] == "admin"
    assert corpo["user"]["status"] == "active"
    # A senha foi escolhida por quem se cadastrou, não veio do ambiente:
    # não há nada para trocar no primeiro login.
    assert corpo["user"]["must_change_password"] is False
    entrada = dono_declarado.post("/api/v1/auth/login", json={
        "email": "dono@arbites.test", "password": SENHA})
    assert entrada.status_code == 200


def test_a_comparacao_do_email_ignora_caixa(dono_declarado):
    r = dono_declarado.post("/api/v1/auth/register", json={
        "email": "Dono@Arbites.Test", "password": SENHA, "name": "Dono"})
    assert r.json()["admin"] is True


def test_outro_email_nao_vira_dono_mesmo_com_o_ambiente_declarado(dono_declarado):
    r = dono_declarado.post("/api/v1/auth/register", json={
        "email": "impostor@arbites.test", "password": SENHA, "name": "X"})
    assert r.json()["admin"] is False
    assert r.json()["user"]["status"] == "pending"


def test_com_admin_ativo_o_email_do_ambiente_nao_reabre_a_porta(ws, monkeypatch):
    """A regra vale UMA vez: com admin ativo, o cadastro volta a ser pendente.

    Sem isto, quem conhecesse o e-mail do ambiente criaria um admin novo a
    qualquer momento, contornando a aprovação.
    """
    monkeypatch.setenv("ARBITES_ADMIN_EMAIL", ADMIN_EMAIL)
    monkeypatch.setenv("ARBITES_ADMIN_PASSWORD", BOOTSTRAP_PASSWORD)
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        assert client.get("/api/v1/auth/me").json()["no_admin"] is False
        r = client.post("/api/v1/auth/register", json={
            "email": "outro@arbites.test", "password": SENHA, "name": "Y"})
        assert r.json()["admin"] is False
        assert r.json()["user"]["status"] == "pending"


def test_a_conta_ja_existente_nao_muda_de_papel_pelo_cadastro(sem_admin):
    """O caso relatado: conta já criada como viewer/pending.

    Recadastrar não conserta (409, e-mail em uso) — quem conserta é o
    comando local. O aviso da tela precisa continuar de pé.
    """
    sem_admin.post("/api/v1/auth/register", json={
        "email": "gcarini@arbites.test", "password": SENHA, "name": "G"})
    de_novo = sem_admin.post("/api/v1/auth/register", json={
        "email": "gcarini@arbites.test", "password": SENHA, "name": "G"})
    assert de_novo.status_code == 409
    assert sem_admin.get("/api/v1/auth/me").json()["no_admin"] is True
