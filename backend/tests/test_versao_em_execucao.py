"""Qual código o processo está rodando (change 0184).

"Atualizei e o erro continua" tem duas leituras — o conserto não funcionou,
ou o conserto não está rodando — e nada distinguia as duas: `__version__` é
fixo desde sempre, então `/health` respondia igual para qualquer commit.
"""

import subprocess

import pytest
from conftest import logged_in_client

from arbites import versao as versao_ops


@pytest.fixture(autouse=True)
def _sem_cache():
    """A identidade é cacheada de propósito (o processo não troca de código
    enquanto vive); os testes precisam recalcular."""
    versao_ops.identidade.cache_clear()
    yield
    versao_ops.identidade.cache_clear()


def test_num_checkout_git_responde_o_commit():
    dados = versao_ops.identidade()
    assert dados["origem"] == "git"
    assert dados["commit"] and len(dados["commit"]) >= 7
    assert dados["branch"]


def test_alteracao_local_nao_commitada_e_declarada():
    """Commit sozinho mentiria por semelhança: o que roda pode não ser o que
    está no commit."""
    assert versao_ops.identidade()["dirty"] in (True, False)


def test_sem_git_diz_isso_em_vez_de_inventar(monkeypatch):
    """Imagem de container ou cópia baixada não têm `.git` ao lado."""
    monkeypatch.setattr(versao_ops, "_git", lambda *a: None)
    dados = versao_ops.identidade()
    assert dados["commit"] is None
    assert "sem checkout" in dados["origem"]
    assert dados["version"]


def test_git_indisponivel_nao_derruba(monkeypatch):
    """O binário do git pode não existir na máquina que roda o servidor."""
    def explode(*a, **k):
        raise FileNotFoundError("git")
    monkeypatch.setattr(subprocess, "run", explode)
    assert versao_ops.identidade()["commit"] is None


def test_a_linha_do_terminal_cabe_em_uma_linha():
    linha = versao_ops.linha()
    assert "\n" not in linha and linha.startswith("Arbites")


def test_o_health_responde_o_commit(ws):
    """É a rota pública: dá para conferir de fora qual código atende."""
    with logged_in_client(ws) as client:
        corpo = client.get("/api/v1/health").json()
        assert corpo["status"] == "ok"
        assert corpo["version"]
        assert "commit" in corpo and "branch" in corpo


def test_o_health_continua_aberto_sem_sessao(ws):
    """Conferir a versão não pode exigir estar logado — o 401 é justamente
    um dos sintomas que se quer diagnosticar."""
    from fastapi.testclient import TestClient

    from arbites.api import create_app

    with TestClient(create_app(ws.root, watch=False)) as anonimo:
        assert anonimo.get("/api/v1/health").status_code == 200
