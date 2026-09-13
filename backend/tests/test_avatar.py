"""Critérios de aceite do avatar de conta (change 0110).

O avatar mora ao lado do perfil, em `profiles/avatars/<slug-do-e-mail>.<ext>`,
e é a única imagem que a instância serve de volta para o navegador — por isso
o formato é decidido por assinatura de bytes, nunca pela extensão que o
cliente informou. Sem imagem não é erro: o cliente desenha o identicon.
"""

import pytest

from arbites import auth as auth_ops
from arbites.api import create_app
from arbites.workspace import slugify
from conftest import ADMIN_EMAIL, login_admin

from fastapi.testclient import TestClient

OTHER = {"email": "outra@arbites.test", "password": "senha-de-outra-conta-1"}

# PNG 1×1 real: cabeçalho de verdade, porque o sniff olha os bytes.
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000a49444154789c6300010000050001"
    "0d0a2db40000000049454e44ae426082"
)
JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\x00" * 32
WEBP = b"RIFF" + (36).to_bytes(4, "little") + b"WEBP" + b"VP8 " + b"\x00" * 24


def _upload(test_client, blob, filename="foto.png", content_type="image/png"):
    return test_client.put(
        "/api/v1/profile/avatar",
        files={"file": (filename, blob, content_type)},
    )


@pytest.fixture()
def other(anon_client):
    """Segunda conta ativa, para provar o isolamento entre contas."""
    auth_ops.create_user(
        anon_client.app.state.auth, OTHER["email"], OTHER["password"],
        role="editor", status="active",
    )
    return OTHER


def _login(test_client, credentials):
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert response.status_code == 200, response.text


# -- AC1: sobe, aparece, sobrevive ao reinício; remover volta ao identicon --


def test_sem_imagem_a_conta_nao_tem_avatar(client):
    """404 aqui é contrato, não falha: é o sinal de 'desenhe o identicon'."""
    resp = client.get("/api/v1/profile/avatar")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "no_avatar"


def test_upload_aparece_e_sobrevive_ao_reinicio(ws):
    app = create_app(ws.root, watch=False)
    with TestClient(app) as first:
        login_admin(first)
        assert _upload(first, PNG).json() == {"ok": True, "format": "png"}
        served = first.get("/api/v1/profile/avatar")
        assert served.status_code == 200 and served.content == PNG

    # o arquivo é o estado: o processo cai, o avatar continua no workspace.
    # O nome começa pelo slug (legível) e leva o sufixo que o torna unívoco
    # (change 0119) — o teste olha o começo, não o sufixo inteiro.
    guardados = list((ws.root / "profiles" / "avatars").glob(
        f"{slugify(ADMIN_EMAIL)}-*.png"))
    assert len(guardados) == 1

    app = create_app(ws.root, watch=False)
    with TestClient(app) as second:
        login_admin(second)
        again = second.get("/api/v1/profile/avatar")
        assert again.status_code == 200 and again.content == PNG


def test_remover_volta_ao_identicon(client):
    _upload(client, PNG)
    assert client.delete("/api/v1/profile/avatar").status_code == 204
    assert client.get("/api/v1/profile/avatar").status_code == 404
    # remover de novo não explode: o estado desejado já é o estado.
    assert client.delete("/api/v1/profile/avatar").status_code == 204


def test_troca_de_formato_nao_deixa_arquivo_orfao(client):
    _upload(client, PNG)
    assert _upload(client, JPEG, "foto.jpg", "image/jpeg").json()["format"] == "jpg"
    avatars = client.ws.root / "profiles" / "avatars"
    assert [p.suffix for p in avatars.glob(f"{slugify(ADMIN_EMAIL)}-*")] == [".jpg"]


def test_webp_tambem_e_aceito(client):
    assert _upload(client, WEBP, "foto.webp", "image/webp").json()["format"] == "webp"


# -- AC2: identidade estável e distinta por conta (a semente do identicon) --


def test_cada_conta_tem_semente_propria_e_estavel(anon_client, other):
    """O identicon é desenhado no cliente a partir do e-mail da sessão. O que
    o backend precisa garantir é o insumo: cada conta enxerga o seu e-mail,
    sempre o mesmo, e nunca o de outra."""
    login_admin(anon_client)
    mine = anon_client.get("/api/v1/auth/me").json()["user"]["email"]
    assert mine == anon_client.get("/api/v1/auth/me").json()["user"]["email"]

    anon_client.post("/api/v1/auth/logout")
    _login(anon_client, other)
    theirs = anon_client.get("/api/v1/auth/me").json()["user"]["email"]
    assert theirs == other["email"] != mine

    # slugs distintos ⇒ arquivos distintos: duas contas nunca se sobrepõem.
    assert slugify(mine) != slugify(theirs)


# -- AC3: isolamento entre contas e recusa de não-imagem ------------------


def test_avatar_de_uma_conta_nao_e_legivel_por_outra(anon_client, other):
    login_admin(anon_client)
    _upload(anon_client, PNG)
    anon_client.post("/api/v1/auth/logout")

    _login(anon_client, other)
    assert anon_client.get("/api/v1/profile/avatar").status_code == 404

    _upload(anon_client, JPEG, "foto.jpg", "image/jpeg")
    anon_client.post("/api/v1/auth/logout")

    login_admin(anon_client)
    mine = anon_client.get("/api/v1/profile/avatar")
    assert mine.status_code == 200 and mine.content == PNG


def test_arquivo_que_nao_e_imagem_e_recusado_mesmo_com_extensao_de_imagem(client):
    payload = b"<svg onload=alert(1)></svg>"
    resp = _upload(client, payload, "ataque.png", "image/png")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_image"
    assert client.get("/api/v1/profile/avatar").status_code == 404


def test_imagem_acima_de_1mb_e_recusada(client):
    grande = PNG + b"\x00" * (1024 * 1024)
    resp = _upload(client, grande)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "avatar_too_large"


def test_avatar_exige_sessao(anon_client):
    assert anon_client.get("/api/v1/profile/avatar").status_code == 401
    assert _upload(anon_client, PNG).status_code == 401


# -- Cache do avatar (change 0117) ---------------------------------------


def test_avatar_declara_cache_privado_com_revalidacao(client):
    """Sem diretiva explícita o navegador aplica cache heurístico e pode
    servir a foto antiga; e um intermediário fica autorizado a guardar
    imagem de UMA conta. `private, no-cache` fecha os dois."""
    _upload(client, PNG)
    resp = client.get("/api/v1/profile/avatar")
    assert resp.headers["cache-control"] == "private, no-cache"
    # o ETag continua lá: revalidar não é o mesmo que baixar de novo
    assert resp.headers.get("etag")


def test_trocar_a_foto_muda_o_etag(client):
    """É o que faz a revalidação valer a pena: mesmo endereço, conteúdo
    novo, e o navegador descobre isso no 304 que não veio."""
    _upload(client, PNG)
    antes = client.get("/api/v1/profile/avatar").headers["etag"]
    _upload(client, JPEG, "foto.jpg", "image/jpeg")
    depois = client.get("/api/v1/profile/avatar")
    assert depois.headers["etag"] != antes
    assert depois.content == JPEG
