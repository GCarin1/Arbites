"""O build do frontend velho, servido em silêncio (change 0182).

`frontend/dist/` não é versionado — é artefato. A consequência é que
`git pull` atualiza o CÓDIGO e não o que o servidor entrega: quem pula o
`npm run build` continua vendo a interface anterior, sem nada dizendo isso.
Um conserto que "não apareceu" fica indistinguível de um que não funcionou.
"""

import os

import pytest
from conftest import logged_in_client

from arbites import build_front


def _frontend(tmp_path, *, com_dist=True, dist_velho=False, com_fonte=True):
    raiz = tmp_path / "frontend"
    if com_fonte:
        (raiz / "src").mkdir(parents=True)
        (raiz / "src" / "App.tsx").write_text("export const x = 1;\n")
    dist = raiz / "dist"
    if com_dist:
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>")
        if dist_velho:
            for arquivo in dist.rglob("*"):
                if arquivo.is_file():
                    os.utime(arquivo, (1, 1))
            os.utime(dist, (1, 1))
    return dist


def test_build_novo_nao_avisa(tmp_path):
    dist = _frontend(tmp_path)
    assert build_front.estado(dist)["desatualizado"] is False
    assert build_front.aviso(dist) is None


def test_codigo_mais_novo_que_o_build_avisa(tmp_path):
    """O caso relatado: pull feito, build esquecido."""
    dist = _frontend(tmp_path, dist_velho=True)
    situacao = build_front.estado(dist)
    assert situacao["desatualizado"] is True
    aviso = build_front.aviso(dist)
    assert aviso["code"] == "frontend_desatualizado"
    # a mensagem traz o comando com o caminho DESTA instalação
    assert "npm --prefix" in aviso["message"]
    assert str(tmp_path) in aviso["message"]


def test_sem_build_nenhum_nao_e_desatualizado(tmp_path):
    """Ausência não é obsolescência: são problemas diferentes."""
    dist = _frontend(tmp_path, com_dist=False)
    situacao = build_front.estado(dist)
    assert situacao["existe"] is False
    assert situacao["desatualizado"] is False
    assert "nenhum build" in situacao["motivo"]


def test_sem_o_fonte_ao_lado_nao_afirma_nada(tmp_path):
    """No container só o `dist` é copiado: sem o código não há o que comparar,
    e a resposta é "não sei", nunca "está velho"."""
    dist = _frontend(tmp_path, com_dist=True, com_fonte=False)
    situacao = build_front.estado(dist)
    assert situacao["desatualizado"] is False
    assert "nada a comparar" in situacao["motivo"]


@pytest.mark.parametrize("arquivo", ["index.html", "package.json", "vite.config.ts"])
def test_o_que_muda_o_bundle_sem_estar_em_src_tambem_conta(tmp_path, arquivo):
    """Trocar a versão de uma dependência exige build novo igual."""
    dist = _frontend(tmp_path, dist_velho=True)
    raiz = dist.parent
    for sobra in (raiz / "src").rglob("*"):
        os.utime(sobra, (1, 1))
    os.utime(raiz / "src", (1, 1))
    assert build_front.estado(dist)["desatualizado"] is False
    (raiz / arquivo).write_text("{}")
    assert build_front.estado(dist)["desatualizado"] is True


def test_node_modules_nao_conta(tmp_path):
    """`npm install` mexe em node_modules e não muda o bundle: contá-lo faria
    o aviso aparecer à toa e ninguém mais olharia para ele."""
    dist = _frontend(tmp_path, dist_velho=True)
    raiz = dist.parent
    for sobra in (raiz / "src").rglob("*"):
        os.utime(sobra, (1, 1))
    os.utime(raiz / "src", (1, 1))
    (raiz / "node_modules" / "alguma-lib").mkdir(parents=True)
    (raiz / "node_modules" / "alguma-lib" / "index.js").write_text("1")
    assert build_front.estado(dist)["desatualizado"] is False


def test_o_aviso_chega_na_lista_de_problemas(ws, tmp_path, monkeypatch):
    """A tela que mostra este aviso é a ANTIGA — e é por isso que ela precisa
    mostrá-lo: a API está atual, quem está velho é o bundle."""
    dist = _frontend(tmp_path, dist_velho=True)
    monkeypatch.setenv("ARBITES_FRONTEND_DIST", str(dist))
    with logged_in_client(ws) as client:
        codigos = [a["code"] for a in client.get("/api/v1/warnings").json()]
        assert "frontend_desatualizado" in codigos


def test_build_em_dia_nao_polui_a_lista(ws, tmp_path, monkeypatch):
    dist = _frontend(tmp_path)
    monkeypatch.setenv("ARBITES_FRONTEND_DIST", str(dist))
    with logged_in_client(ws) as client:
        codigos = [a["code"] for a in client.get("/api/v1/warnings").json()]
        assert "frontend_desatualizado" not in codigos
