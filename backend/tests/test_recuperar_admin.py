"""Recuperar o acesso na própria máquina (change 0166).

"Por que 401?" tem TRÊS respostas — conta inexistente, senha errada e conta
não-ativa — e a API não distingue nenhuma delas de fora, de propósito: separar
"não existe" de "senha errada" entrega uma lista de contas válidas a quem
tenta adivinhar. De dentro da máquina, porém, isso vira um mistério sem saída.
"""

import subprocess
import sys

import pytest
from conftest import ADMIN_EMAIL
from fastapi.testclient import TestClient

from arbites import auth as auth_ops
from arbites.api import create_app


def _arbites(ws, *args, cwd=None) -> subprocess.CompletedProcess:
    import os
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith("ARBITES_")}
    env["PYTHONPATH"] = str(raiz)
    return subprocess.run(
        [sys.executable, "-m", "arbites", *args, "--workspace", str(ws.root)],
        cwd=str(cwd or raiz), env=env, capture_output=True, text=True,
    )


def test_workspace_sem_conta_explica_o_401(ws):
    """O caso em que a instância sobe e NINGUÉM consegue entrar."""
    r = _arbites(ws, "admin")
    assert "NENHUMA conta existe" in r.stdout
    assert "401" in r.stdout
    assert "--password" in r.stdout  # e ensina o comando que resolve


def test_criar_o_primeiro_admin_pela_linha_de_comando(ws):
    r = _arbites(ws, "admin", "--email", "novo@arbites.test",
                 "--password", "uma-senha-longa-1")
    assert "CRIADA" in r.stdout, r.stdout

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        entrada = client.post("/api/v1/auth/login", json={
            "email": "novo@arbites.test", "password": "uma-senha-longa-1"})
        assert entrada.status_code == 200


def test_redefinir_a_senha_de_quem_ja_existe(ws):
    """O caminho traiçoeiro: a conta existe, e por isso o bootstrap por
    ambiente NUNCA mais toca nela — mudar a senha no .env não muda nada."""
    _arbites(ws, "admin", "--email", "dono@arbites.test",
             "--password", "a-senha-antiga-1")
    r = _arbites(ws, "admin", "--email", "dono@arbites.test",
                 "--password", "a-senha-nova-2")
    assert "SENHA REDEFINIDA" in r.stdout, r.stdout

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={
            "email": "dono@arbites.test", "password": "a-senha-antiga-1"
        }).status_code == 401
        assert client.post("/api/v1/auth/login", json={
            "email": "dono@arbites.test", "password": "a-senha-nova-2"
        }).status_code == 200


def test_conta_inativa_volta_a_ativa_e_a_admin(ws):
    """Conta pendente responde 401 igual a senha errada — e fica assim para
    sempre se não houver outro admin para aprová-la."""
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json={
            "email": "pendente@arbites.test", "password": "senha-de-espera-1",
            "name": "Pendente"})
        assert client.post("/api/v1/auth/login", json={
            "email": "pendente@arbites.test", "password": "senha-de-espera-1"
        }).status_code == 401

    r = _arbites(ws, "admin", "--email", "pendente@arbites.test",
                 "--password", "agora-vai-entrar-1")
    assert "admin/ativa" in r.stdout

    app2 = create_app(ws.root, watch=False)
    with TestClient(app2) as client:
        assert client.post("/api/v1/auth/login", json={
            "email": "pendente@arbites.test", "password": "agora-vai-entrar-1"
        }).status_code == 200


def test_senha_curta_e_recusada_sem_tocar_na_conta(ws):
    _arbites(ws, "admin", "--email", "dono@arbites.test",
             "--password", "a-senha-boa-1")
    r = _arbites(ws, "admin", "--email", "dono@arbites.test", "--password", "curta")
    assert r.returncode == 2
    assert "12 caracteres" in r.stdout

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={
            "email": "dono@arbites.test", "password": "a-senha-boa-1"
        }).status_code == 200


def test_redefinir_tambem_destrava_o_bloqueio(ws):
    """Quem chegou aqui provavelmente errou a senha várias vezes — exigir um
    segundo comando depois de consertar a senha seria pedir o óbvio."""
    _arbites(ws, "admin", "--email", "dono@arbites.test",
             "--password", "a-senha-boa-1")
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        for _ in range(6):
            client.post("/api/v1/auth/login", json={
                "email": "dono@arbites.test", "password": "errada"})
        assert client.post("/api/v1/auth/login", json={
            "email": "dono@arbites.test", "password": "a-senha-boa-1"
        }).status_code == 429

    _arbites(ws, "admin", "--email", "dono@arbites.test",
             "--password", "a-senha-nova-2")
    app2 = create_app(ws.root, watch=False)
    with TestClient(app2) as client:
        assert client.post("/api/v1/auth/login", json={
            "email": "dono@arbites.test", "password": "a-senha-nova-2"
        }).status_code == 200


def test_listar_nunca_mostra_senha_nem_hash(ws):
    _arbites(ws, "admin", "--email", "dono@arbites.test",
             "--password", "a-senha-secreta-1")
    r = _arbites(ws, "admin")
    assert "a-senha-secreta-1" not in r.stdout
    assert "hash" not in r.stdout.lower()
    assert "dono@arbites.test" in r.stdout
