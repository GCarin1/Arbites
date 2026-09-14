"""Primeira execução fora do container (change 0165).

Dois sintomas, uma causa: o `.env` nunca era lido pelo produto — quem lê o
arquivo no Docker é o **Compose**, não o Arbites. Fora do container as
credenciais de bootstrap chegavam vazias, nenhum admin era criado EM SILÊNCIO,
e a pessoa tentava entrar numa conta que nunca existiu até se trancar por
tentativas.
"""

import os

import pytest
from conftest import ADMIN_EMAIL, login_admin
from fastapi.testclient import TestClient

from arbites import auth as auth_ops
from arbites.api import create_app
from arbites.envfile import carregar, parse


# -- o arquivo ---------------------------------------------------------------


def test_parse_do_formato_minimo():
    lido = parse(
        "# comentário\n"
        "\n"
        "ARBITES_ADMIN_EMAIL=gcarini@arbites.local\n"
        'ARBITES_ADMIN_PASSWORD="senha com espaço"\n'
        "ARBITES_SIGNUP='off'\n"
        "  ESPACOS_EM_VOLTA = valor \n"
        "linha sem igual\n"
        "CHAVE-INVALIDA=x\n"
    )
    assert lido == {
        "ARBITES_ADMIN_EMAIL": "gcarini@arbites.local",
        "ARBITES_ADMIN_PASSWORD": "senha com espaço",
        "ARBITES_SIGNUP": "off",
        "ESPACOS_EM_VOLTA": "valor",
    }


def test_o_ambiente_do_processo_ganha_do_arquivo(tmp_path, monkeypatch):
    """Quem exportou a variável na mão quis AQUELE valor agora; um `.env`
    esquecido no diretório não pode vencê-la em silêncio."""
    (tmp_path / ".env").write_text(
        "ARBITES_ADMIN_EMAIL=do-arquivo@x.test\nOUTRA=do-arquivo\n",
        encoding="utf-8")
    monkeypatch.setenv("ARBITES_ADMIN_EMAIL", "do-ambiente@x.test")
    monkeypatch.delenv("OUTRA", raising=False)

    aplicadas = carregar(tmp_path)

    assert os.environ["ARBITES_ADMIN_EMAIL"] == "do-ambiente@x.test"
    assert os.environ["OUTRA"] == "do-arquivo"
    assert aplicadas == ["OUTRA"]  # a que já existia não é tocada


def test_sem_arquivo_nao_acontece_nada(tmp_path):
    assert carregar(tmp_path) == []


def test_carregar_devolve_as_chaves_e_nunca_os_valores(tmp_path, monkeypatch):
    """Este arquivo costuma ter senha dentro: o que sai para o log é o nome
    da variável, não o conteúdo."""
    (tmp_path / ".env").write_text(
        "ARBITES_ADMIN_PASSWORD=segredo-que-nao-pode-vazar\n", encoding="utf-8")
    monkeypatch.delenv("ARBITES_ADMIN_PASSWORD", raising=False)

    aplicadas = carregar(tmp_path)
    assert aplicadas == ["ARBITES_ADMIN_PASSWORD"]
    assert "segredo-que-nao-pode-vazar" not in " ".join(aplicadas)


def test_arquivo_ilegivel_nao_derruba_o_arranque(tmp_path):
    (tmp_path / ".env").mkdir()  # um diretório chamado .env
    assert carregar(tmp_path) == []


# -- o arranque sem credencial deixou de ser silencioso ----------------------


def test_sem_admin_e_sem_credencial_o_arranque_reclama(ws, monkeypatch, caplog):
    """Antes era um no-op mudo: a instância subia sem conta nenhuma e a pessoa
    ia tentar entrar numa conta que nunca existiu."""
    monkeypatch.delenv("ARBITES_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ARBITES_ADMIN_PASSWORD", raising=False)

    with caplog.at_level("ERROR"):
        with TestClient(create_app(ws.root, watch=False)):
            pass

    texto = caplog.text
    assert "NENHUMA conta de administrador" in texto
    assert "ARBITES_ADMIN_EMAIL" in texto
    assert ".env" in texto


def test_com_credencial_o_admin_nasce_e_nao_ha_reclamacao(ws, caplog):
    with caplog.at_level("ERROR"):
        with TestClient(create_app(ws.root, watch=False)):
            pass
    assert "NENHUMA conta de administrador" not in caplog.text


# -- a saída do bloqueio -----------------------------------------------------


def test_bloqueio_por_tentativas_e_destravavel(ws):
    """Sem esta saída, um erro de senha na própria máquina vira quinze minutos
    de espera sem nenhuma explicação de como encurtar."""
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        for _ in range(6):
            client.post("/api/v1/auth/login",
                        json={"email": ADMIN_EMAIL, "password": "errada"})
        barrado = client.post("/api/v1/auth/login",
                              json={"email": ADMIN_EMAIL, "password": "errada"})
        assert barrado.status_code == 429

        assert auth_ops.clear_attempts(app.state.auth, ADMIN_EMAIL) > 0

        # e agora a senha certa entra
        login_admin(client)


def test_destravar_uma_conta_nao_destrava_as_outras(ws):
    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        for email in (ADMIN_EMAIL, "outro@arbites.test"):
            for _ in range(6):
                client.post("/api/v1/auth/login",
                            json={"email": email, "password": "errada"})

        auth_ops.clear_attempts(app.state.auth, ADMIN_EMAIL)
        restantes = auth_ops.list_attempts(app.state.auth, limit=500)
        assert all(a["email"] != ADMIN_EMAIL for a in restantes)
        assert any(a["email"] == "outro@arbites.test" for a in restantes)
