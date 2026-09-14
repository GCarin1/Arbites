"""Instância sem cofre do sistema operacional (change 0160).

O defeito: num container não há keychain nenhum, e `keyring` levanta
`NoKeyringError` na primeira chamada. Como a tela Problemas passou a
perguntar pelo estado da credencial em TODO carregamento (change 0157), a
pergunta explodia e derrubava a aplicação inteira com 500.

A lição que os testes abaixo fixam: ausência de cofre é uma RESPOSTA
legítima — "não há credencial" — e não um acidente.
"""

import pytest
from conftest import login_admin
from fastapi.testclient import TestClient

from arbites.api import create_app
from arbites.ci import ENV_TOKEN, CIError, TokenStore
from arbites.workspace import Workspace


@pytest.fixture()
def sem_cofre(monkeypatch):
    """Nenhum backend de keyring — exatamente o que a imagem Docker tem."""
    import keyring
    import keyring.backends.fail

    anterior = keyring.get_keyring()
    keyring.set_keyring(keyring.backends.fail.Keyring())
    monkeypatch.delenv(ENV_TOKEN, raising=False)
    yield
    keyring.set_keyring(anterior)


@pytest.fixture()
def app_sem_cofre(ws, sem_cofre):
    app = create_app(ws.root, watch=False, token_store=TokenStore())
    with TestClient(app) as client:
        login_admin(client)
        yield client


# -- o defeito que derrubou a aplicação --------------------------------------


def test_a_tela_de_problemas_responde_sem_cofre(app_sem_cofre):
    """A regressão exata: /warnings devolvia 500 e a aplicação inteira caía,
    porque essa rota carrega em toda navegação."""
    r = app_sem_cofre.get("/api/v1/warnings")
    assert r.status_code == 200


def test_o_status_do_token_responde_sem_cofre(app_sem_cofre):
    r = app_sem_cofre.get("/api/v1/settings/github/token")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["configured"] is False
    assert corpo["storable"] is False   # ler funciona; GUARDAR não
    assert corpo["source"] is None


def test_a_falta_de_cofre_vira_problema_com_a_saida(app_sem_cofre):
    """Campo que recusa em silêncio quando alguém tenta usar é pior do que
    um problema dito na entrada."""
    problema = next(w for w in app_sem_cofre.get("/api/v1/warnings").json()
                    if w["code"] == "ci_credential_no_store")
    assert ENV_TOKEN in problema["message"]
    assert "docker-compose" in problema["message"]


def test_guardar_token_sem_cofre_recusa_explicando(app_sem_cofre):
    r = app_sem_cofre.put("/api/v1/settings/github/token",
                          json={"token": "ghp_qualquer"})
    assert r.status_code == 409
    erro = r.json()["error"]
    assert erro["code"] == "no_keyring"
    assert ENV_TOKEN in erro["message"]


# -- a saída: a credencial pelo ambiente do processo -------------------------


def test_token_do_ambiente_funciona_onde_nao_ha_cofre(ws, sem_cofre, monkeypatch):
    monkeypatch.setenv(ENV_TOKEN, "ghp_do_ambiente")
    app = create_app(ws.root, watch=False, token_store=TokenStore())
    with TestClient(app) as client:
        login_admin(client)
        estado = client.get("/api/v1/settings/github/token").json()
        assert estado["configured"] is True
        assert estado["source"] == "env"
        # e o problema sai da tela, porque deixou de existir
        assert [w for w in client.get("/api/v1/warnings").json()
                if w["code"] == "ci_credential_no_store"] == []


def test_o_ambiente_ganha_do_cofre(monkeypatch):
    """Quem definiu a variável quis AQUELE token; um resto esquecido no cofre
    não pode ganhar dela em silêncio."""
    guardados = {}

    class CofreFalso(TokenStore):
        def set(self, token):
            guardados["pat"] = token

        def get(self):
            import os
            do_ambiente = (os.environ.get(ENV_TOKEN) or "").strip()
            return do_ambiente or guardados.get("pat")

    loja = CofreFalso()
    loja.set("do-cofre")
    assert loja.get() == "do-cofre"

    monkeypatch.setenv(ENV_TOKEN, "do-ambiente")
    assert loja.get() == "do-ambiente"


def test_o_valor_do_token_nunca_volta_na_resposta(ws, sem_cofre, monkeypatch):
    """A regra da ADR 0008 continua valendo com a credencial vindo do
    ambiente: status sim, valor nunca."""
    import json

    monkeypatch.setenv(ENV_TOKEN, "ghp_SEGREDO_DO_AMBIENTE")
    app = create_app(ws.root, watch=False, token_store=TokenStore())
    with TestClient(app) as client:
        login_admin(client)
        corpo = json.dumps(client.get("/api/v1/settings/github/token").json())
        assert "ghp_SEGREDO_DO_AMBIENTE" not in corpo
        assert "ghp_SEGREDO_DO_AMBIENTE" not in json.dumps(
            client.get("/api/v1/warnings").json())


def test_token_do_ambiente_nao_escreve_nada_no_workspace(ws, sem_cofre, monkeypatch):
    """O workspace é versionável (ADR 0008): o segredo não pode encostar nele
    nem quando chega por variável de ambiente."""
    from pathlib import Path

    segredo = "ghp_NAO_PODE_TOCAR_O_DISCO"
    monkeypatch.setenv(ENV_TOKEN, segredo)
    app = create_app(ws.root, watch=False, token_store=TokenStore())
    with TestClient(app) as client:
        login_admin(client)
        client.get("/api/v1/settings/github/token")
        client.get("/api/v1/warnings")
    for caminho in Path(ws.root).rglob("*"):
        if caminho.is_file():
            try:
                conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            assert segredo not in conteudo, f"token vazou em {caminho}"


# -- com cofre, nada muda ----------------------------------------------------


def test_com_cofre_o_comportamento_e_o_de_sempre(client):
    estado = client.get("/api/v1/settings/github/token").json()
    assert estado["storable"] is True
    assert [w for w in client.get("/api/v1/warnings").json()
            if w["code"] == "ci_credential_no_store"] == []
