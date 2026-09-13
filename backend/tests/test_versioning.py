"""Critérios de aceite do versionamento do workspace (change 0112).

O workspace vira um repositório git de verdade: um commit por AÇÃO da
interface, histórico por caso de teste, comparação entre versões e volta
atrás. Registro nunca derruba escrita — um workspace onde o git não
funciona continua aceitando criar e editar casos.
"""

import subprocess

import pytest

from arbites import versioning
from arbites.api import create_app
from conftest import ADMIN_EMAIL, login_admin

from fastapi.testclient import TestClient

TC_BODY = (
    "## Objetivo\n\nValidar.\n\n## Passos\n\n1. Abrir a tela\n2. Agir\n\n"
    "## Resultado esperado\n\nOk.\n"
)

pytestmark = pytest.mark.skipif(
    subprocess.run(["git", "--version"], capture_output=True).returncode != 0,
    reason="git nao disponivel no ambiente",
)


def make_ct(client, title="Login", **extra):
    return client.post(
        "/api/v1/testcases", json={"title": title, "body": TC_BODY, **extra}
    ).json()


def git(ws, *args):
    return subprocess.run(
        ["git", *args], cwd=str(ws.root), capture_output=True, text=True,
    ).stdout


def subjects(ws):
    return git(ws, "log", "--pretty=format:%s").splitlines()


# -- AC1: um commit por ação, assinado pela sessão, sem o índice ----------


def test_criar_editar_e_mover_geram_um_commit_por_acao(client):
    ct = make_ct(client, "Login")
    client.put(f"/api/v1/testcases/{ct['id']}", json={"priority": "critical"})
    client.post(f"/api/v1/testcases/{ct['id']}/move", json={"folder": "regressao"})

    mensagens = subjects(client.ws)
    assert f"cria {ct['id']}: Login" in mensagens
    assert f"edita {ct['id']}: Login" in mensagens
    assert f"move {ct['id']} para regressao" in mensagens
    # uma ação, um commit: a edição não virou dois por causa do reindex
    assert mensagens.count(f"edita {ct['id']}: Login") == 1


def test_commit_e_assinado_com_o_autor_da_sessao(client):
    make_ct(client, "Login")
    assert ADMIN_EMAIL in git(client.ws, "log", "-1", "--pretty=format:%ae")


def test_indice_descartavel_fica_fora_do_repositorio(client):
    make_ct(client, "Login")
    versionados = git(client.ws, "ls-files")
    assert ".arbites/" not in versionados
    assert "index.db" not in versionados
    assert ".gitignore" in versionados
    # e o índice realmente existe no disco — ele só não é versionado
    assert client.ws.index_db_path.exists()


def test_excluir_registra_a_saida_sem_apagar_do_disco(client):
    ct = make_ct(client, "Login")
    client.delete(f"/api/v1/testcases/{ct['id']}")
    assert f"exclui {ct['id']}" in subjects(client.ws)
    # a lixeira continua sendo a lixeira (o commit só registra que saiu)
    assert list(client.ws.trash_dir.iterdir())


# -- AC2: histórico, comparação e restauração ----------------------------


def test_historico_lista_as_versoes_do_caso(client):
    ct = make_ct(client, "Login")
    client.put(f"/api/v1/testcases/{ct['id']}", json={"title": "Login com 2FA"})

    versoes = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]
    assert [v["message"] for v in versoes][:2] == [
        f"edita {ct['id']}: Login com 2FA",
        f"cria {ct['id']}: Login",
    ]
    assert versoes[0]["email"] == ADMIN_EMAIL
    assert len(versoes[0]["short"]) == 8


def test_historico_sobrevive_a_mudanca_de_pasta(client):
    """`--follow`: mover preserva o ID, e deveria preservar o passado."""
    ct = make_ct(client, "Login")
    client.post(f"/api/v1/testcases/{ct['id']}/move", json={"folder": "regressao"})
    versoes = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]
    assert f"cria {ct['id']}: Login" in [v["message"] for v in versoes]


def test_comparacao_entre_duas_versoes_mostra_a_linha_alterada(client):
    ct = make_ct(client, "Login")
    client.put(f"/api/v1/testcases/{ct['id']}", json={"priority": "critical"})
    versoes = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]

    saida = client.get(
        f"/api/v1/testcases/{ct['id']}/versions/diff",
        params={"a": versoes[1]["sha"], "b": versoes[0]["sha"]},
    ).text
    assert "-priority: medium" in saida
    assert "+priority: critical" in saida


def test_conteudo_de_uma_versao_antiga_e_recuperavel(client):
    ct = make_ct(client, "Login")
    client.put(f"/api/v1/testcases/{ct['id']}", json={"title": "Login com 2FA"})
    versoes = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]

    antigo = client.get(f"/api/v1/testcases/{ct['id']}/versions/{versoes[1]['sha']}").text
    assert "title: Login" in antigo and "2FA" not in antigo


def test_restaurar_devolve_o_conteudo_gravando_um_commit_novo(client):
    ct = make_ct(client, "Login")
    client.put(f"/api/v1/testcases/{ct['id']}", json={"title": "Login com 2FA"})
    versoes = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]
    original = versoes[-1]["sha"]

    restaurado = client.post(
        f"/api/v1/testcases/{ct['id']}/versions/{original}/restore"
    ).json()
    assert restaurado["title"] == "Login"

    depois = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]
    # histórico PRESERVADO: a restauração é um commit a mais, não uma reescrita
    assert len(depois) == len(versoes) + 1
    assert depois[0]["message"].startswith(f"restaura testcases/{ct['id']}")
    assert f"edita {ct['id']}: Login com 2FA" in [v["message"] for v in depois]


def test_sha_que_nao_existe_devolve_404(client):
    ct = make_ct(client, "Login")
    resp = client.get(f"/api/v1/testcases/{ct['id']}/versions/0000000000000000000000")
    assert resp.status_code == 404


# -- AC3: edição externa e workspace sem git -----------------------------


def test_edicao_por_fora_entra_como_commit_de_autoria_externa(client):
    """Editar no Obsidian é editar a fonte da verdade; não deveria sumir."""
    ct = make_ct(client, "Login")
    rel = client.app.state.conn.execute(
        "SELECT path FROM testcases WHERE id = ?", (ct["id"],)
    ).fetchone()["path"]
    caminho = client.ws.root / rel
    caminho.write_text(
        caminho.read_text(encoding="utf-8").replace("Agir", "Agir por fora"),
        encoding="utf-8",
    )

    versoes = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]
    assert versoes[0]["message"] == f"edicao externa: {rel}"
    assert versoes[0]["email"] == "externo@workspace"


def test_historico_sem_edicao_pendente_nao_inventa_commit(client):
    ct = make_ct(client, "Login")
    antes = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]
    depois = client.get(f"/api/v1/testcases/{ct['id']}/versions").json()["versions"]
    assert len(antes) == len(depois)


def test_workspace_sem_git_continua_aceitando_criar_e_editar(ws, monkeypatch):
    """Registro que derruba a escrita do usuário é pior do que registro
    nenhum: sem git, o caso é criado e editado do mesmo jeito."""
    def sem_git(*args, **kwargs):
        raise OSError("git nao instalado")

    monkeypatch.setattr(versioning.subprocess, "run", sem_git)

    app = create_app(ws.root, watch=False)
    with TestClient(app) as client:
        login_admin(client)
        ct = client.post(
            "/api/v1/testcases", json={"title": "Login", "body": TC_BODY}
        )
        assert ct.status_code == 201
        editado = client.put(
            f"/api/v1/testcases/{ct.json()['id']}", json={"priority": "critical"}
        )
        assert editado.status_code == 200 and editado.json()["priority"] == "critical"
        # e o histórico simplesmente vem vazio, sem explodir
        versoes = client.get(f"/api/v1/testcases/{ct.json()['id']}/versions")
        assert versoes.status_code == 200 and versoes.json()["versions"] == []
