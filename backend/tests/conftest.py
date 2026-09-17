import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from arbites.api import create_app  # noqa: E402
from arbites.indexer import connect, reindex_full  # noqa: E402
from arbites.workspace import Workspace  # noqa: E402


@pytest.fixture()
def ws(tmp_path) -> Workspace:
    workspace = Workspace(tmp_path / "workspace")
    workspace.ensure()
    return workspace


# Credenciais do admin que a suite usa. O gate de sessao vale para todos os
# testes: em vez de desligar a autenticacao (o que deixaria o gate sem prova
# contra as rotas reais), a fixture faz o fluxo de verdade — bootstrap,
# login, troca da senha obrigatoria — e entrega um cliente ja logado.
ADMIN_EMAIL = "admin@arbites.test"
BOOTSTRAP_PASSWORD = "bootstrap-inicial-1"
ADMIN_PASSWORD = "senha-de-teste-longa-1"


@pytest.fixture(autouse=True)
def auth_env(monkeypatch):
    """Todo app montado num teste nasce com o admin de bootstrap disponivel,
    inclusive os rigs que chamam create_app por conta propria."""
    monkeypatch.setenv("ARBITES_ADMIN_EMAIL", ADMIN_EMAIL)
    monkeypatch.setenv("ARBITES_ADMIN_PASSWORD", BOOTSTRAP_PASSWORD)
    monkeypatch.delenv("ARBITES_AUTH", raising=False)
    monkeypatch.delenv("ARBITES_SIGNUP", raising=False)


@contextmanager
def logged_in_client(ws, **kwargs):
    """Monta um app e entrega um cliente ja autenticado como admin.

    Os rigs que precisam de create_app com argumentos proprios (transport de
    IA, key store falso, cliente GitHub) usam este helper em vez de repetir
    o fluxo de login em cada arquivo.
    """
    app = create_app(ws.root, watch=False, **kwargs)
    with TestClient(app) as test_client:
        test_client.ws = ws
        login_admin(test_client)
        yield test_client


@pytest.fixture()
def anon_client(ws):
    """Cliente sem sessao, com o admin de bootstrap ja provisionado."""
    app = create_app(ws.root, watch=False)
    with TestClient(app) as test_client:
        test_client.ws = ws
        yield test_client


def login_admin(test_client) -> None:
    """Entra como o admin de bootstrap e resolve a troca de senha obrigatoria."""
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": BOOTSTRAP_PASSWORD},
    )
    if response.status_code == 200:
        test_client.post(
            "/api/v1/auth/password",
            json={"current_password": BOOTSTRAP_PASSWORD,
                  "new_password": ADMIN_PASSWORD},
        )
        return
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text


@pytest.fixture()
def client(anon_client):
    login_admin(anon_client)
    return anon_client


def make_md(path, meta: dict, body: str = "") -> None:
    """Escreve um .md com frontmatter à mão (simula edição externa)."""
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{yaml.safe_dump(meta, allow_unicode=True)}---\n\n{body}",
        encoding="utf-8",
    )


@pytest.fixture()
def indexed(ws):
    conn = connect(ws)
    reindex_full(ws, conn)
    return conn


@pytest.fixture()
def ca_de_teste(tmp_path):
    """Um certificado de CA de VERDADE, em arquivo.

    `ssl.load_verify_locations` recusa qualquer coisa que não seja um bundle
    real, então um `-----BEGIN CERTIFICATE-----` de mentira não serve para
    exercitar o caminho feliz (change 0186).
    """
    import subprocess

    destino = tmp_path / "ca-de-teste.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", "/dev/null", "-out", str(destino), "-days", "1",
         "-subj", "/CN=CA-de-teste"],
        check=True, capture_output=True,
    )
    return destino
