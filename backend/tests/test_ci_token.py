"""Spec ci-automation — PAT no keyring, nunca exposto (ADR 0008)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from arbites.api import create_app
from arbites.ci import TokenStore
from arbites.workspace import Workspace

from conftest import login_admin


class FakeTokenStore(TokenStore):
    def __init__(self):
        self._token = None

    def set(self, token):
        self._token = token

    def get(self):
        return self._token


@pytest.fixture()
def token_client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    store = FakeTokenStore()
    app = create_app(ws.root, watch=False, token_store=store,
                     github_client=object())
    with TestClient(app) as client:
        login_admin(client)
        client.store = store
        client.ws = ws
        yield client


def test_token_roundtrip_never_returns_value(token_client):
    """O invariante é o NOME do teste: o valor nunca volta.

    A asserção era sobre a FORMA exata da resposta (`== {"configured": False}`)
    e quebrou quando o status ganhou a validade da credencial (change 0157) —
    um campo que existe justamente para ser visto. Prender a forma inteira faz
    o teste falhar por acréscimo legítimo e não falharia se o segredo vazasse
    num campo novo; prender o invariante falha exatamente no caso certo.
    """
    antes = token_client.get("/api/v1/settings/github/token").json()
    assert antes["configured"] is False

    secret = "github_pat_SEGREDO_XYZ"
    resp = token_client.put(
        "/api/v1/settings/github/token", json={"token": secret}
    )
    assert resp.status_code == 200
    assert resp.json()["configured"] is True
    assert secret not in resp.text

    status = token_client.get("/api/v1/settings/github/token")
    assert status.json()["configured"] is True
    assert secret not in status.text
    # nenhum campo do status carrega o valor, nem os que vierem depois
    assert secret not in json.dumps(status.json())
    # foi para o store (keyring em produção), e o valor está lá
    assert token_client.store.get() == secret


def test_token_never_written_inside_workspace(token_client):
    secret = "github_pat_NUNCA_NO_DISCO"
    token_client.put("/api/v1/settings/github/token", json={"token": secret})
    ws: Workspace = token_client.ws
    for path in Path(ws.root).rglob("*"):
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            assert secret not in content, f"token vazou em {path}"
