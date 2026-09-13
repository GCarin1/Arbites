"""Critérios de aceite da identidade de arquivo por conta (change 0119).

`slugify` colapsa qualquer pontuação no mesmo hífen: `ana.silva@x.com` e
`ana-silva@x.com` davam o mesmo texto. Como o perfil mora em
`profiles/<slug>.md` e o avatar em `profiles/avatars/<slug>.<ext>`, duas
contas distintas resolviam o mesmo caminho e compartilhavam perfil, memória
de IA e avatar — o oposto do que o spec já exigia.
"""

import pytest

from arbites import auth as auth_ops
from arbites.api import create_app
from arbites.workspace import Workspace, slugify
from conftest import login_admin

from fastapi.testclient import TestClient

from test_avatar import JPEG, PNG

# Os dois e-mails que davam o MESMO slug — a colisão que abriu o buraco.
ANA = {"email": "ana.silva@arbites.test", "password": "senha-longa-da-ana-1"}
OUTRO = {"email": "ana-silva@arbites.test", "password": "senha-longa-do-outro-1"}

MEMORIA_DA_ANA = "## Contexto Ativo\n\n- negociação salarial em andamento\n"


def _cria(client, cred):
    auth_ops.create_user(
        client.app.state.auth, cred["email"], cred["password"],
        role="editor", status="active",
    )


def _entra(client, cred):
    client.post("/api/v1/auth/logout")
    resp = client.post("/api/v1/auth/login", json={
        "email": cred["email"], "password": cred["password"]})
    assert resp.status_code == 200, resp.text


@pytest.fixture()
def duas_contas(anon_client):
    for cred in (ANA, OUTRO):
        _cria(anon_client, cred)
    return anon_client


def test_os_dois_emails_realmente_colidem_no_slug(duas_contas):
    """A premissa do teste, fixada aqui para que a prova não fique
    silenciosamente vazia se o slugify mudar um dia."""
    assert slugify(ANA["email"]) == slugify(OUTRO["email"])


# -- AC1: contas que colidem no slug ficam separadas ---------------------


def test_a_memoria_de_uma_conta_nao_vaza_para_a_outra(duas_contas):
    client = duas_contas
    _entra(client, ANA)
    client.put("/api/v1/profile", json={"name": "Ana", "memory": MEMORIA_DA_ANA})

    _entra(client, OUTRO)
    perfil = client.get("/api/v1/profile").json()
    assert perfil["name"] == ""
    assert "negociação salarial" not in perfil["memory"]


def test_uma_conta_nao_sobrescreve_o_perfil_da_outra(duas_contas):
    client = duas_contas
    _entra(client, ANA)
    client.put("/api/v1/profile", json={"name": "Ana", "memory": MEMORIA_DA_ANA})

    _entra(client, OUTRO)
    client.put("/api/v1/profile", json={"name": "Outro"})

    _entra(client, ANA)
    de_volta = client.get("/api/v1/profile").json()
    assert de_volta["name"] == "Ana"
    assert "negociação salarial" in de_volta["memory"]


def test_o_avatar_de_uma_conta_nao_e_servido_para_a_outra(duas_contas):
    client = duas_contas
    _entra(client, ANA)
    client.put("/api/v1/profile/avatar", files={"file": ("a.png", PNG, "image/png")})

    _entra(client, OUTRO)
    assert client.get("/api/v1/profile/avatar").status_code == 404

    client.put("/api/v1/profile/avatar", files={"file": ("b.jpg", JPEG, "image/jpeg")})
    _entra(client, ANA)
    meu = client.get("/api/v1/profile/avatar")
    assert meu.status_code == 200 and meu.content == PNG


def test_cada_conta_tem_seu_proprio_arquivo_no_disco(duas_contas):
    client = duas_contas
    for cred in (ANA, OUTRO):
        _entra(client, cred)
        client.put("/api/v1/profile", json={"name": cred["email"]})

    arquivos = sorted(p.name for p in (client.ws.root / "profiles").glob("*.md"))
    assert len(arquivos) == 2, arquivos
    # e o nome continua legível: o slug na frente diz de quem é o arquivo
    assert all(nome.startswith(slugify(ANA["email"])) for nome in arquivos)


# -- AC2: o arquivo gravado sob o nome antigo é adotado ------------------


def test_perfil_gravado_no_nome_antigo_continua_sendo_da_conta(ws):
    """Sem adoção, a atualização apagaria do mapa a memória já escrita: o
    arquivo continuaria no disco, mas ninguém mais o leria."""
    antigo = ws.root / "profiles" / f"{slugify(ANA['email'])}.md"
    antigo.parent.mkdir(parents=True, exist_ok=True)
    antigo.write_text(
        f"---\nname: Ana\n---\n\n{MEMORIA_DA_ANA}", encoding="utf-8"
    )

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        login_admin(client)
        _cria(client, ANA)
        _entra(client, ANA)
        perfil = client.get("/api/v1/profile").json()
        assert perfil["name"] == "Ana"
        assert "negociação salarial" in perfil["memory"]

    assert not antigo.exists()  # foi adotado, não duplicado


def test_avatar_gravado_no_nome_antigo_continua_sendo_da_conta(ws):
    antigo = ws.root / "profiles" / "avatars" / f"{slugify(ANA['email'])}.png"
    antigo.parent.mkdir(parents=True, exist_ok=True)
    antigo.write_bytes(PNG)

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        login_admin(client)
        _cria(client, ANA)
        _entra(client, ANA)
        servido = client.get("/api/v1/profile/avatar")
        assert servido.status_code == 200 and servido.content == PNG


def test_adocao_nao_rouba_arquivo_de_quem_ja_tem_o_seu(ws):
    """Quem já foi migrado não é atropelado por um arquivo antigo homônimo."""
    pasta = ws.root / "profiles"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"{slugify(ANA['email'])}.md").write_text(
        "---\nname: Antigo\n---\n\nvelho\n", encoding="utf-8")

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        login_admin(client)
        _cria(client, ANA)
        _entra(client, ANA)
        client.put("/api/v1/profile", json={"name": "Ana", "memory": "novo"})
        # segunda leitura: o arquivo novo já existe e não é substituído
        assert client.get("/api/v1/profile").json()["name"] == "Ana"
