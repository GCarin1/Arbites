"""Bundle de CA apontado mas inutilizável (change 0186).

O relato: "inseri as variáveis, coloquei o caminho do .pem, e a tela pediu
para eu definir as variáveis de ambiente". A mensagem mandava fazer o que já
tinha sido feito — quem recebe isso conclui, com razão, que a ferramenta não
está lendo o `.env`.

A causa era minha: `ca_bundle()` ignorava em silêncio um caminho que não
resolvia, e a explicação só tinha dois ramos (declarado / não declarado). Um
caminho errado caía no ramo "não declarado".
"""

import pytest
from conftest import logged_in_client

from arbites import tls as tls_ops


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    for nome in tls_ops.VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)


# -- os três estados ---------------------------------------------------------

def test_nada_declarado_nao_e_problema():
    assert tls_ops.problema_do_bundle() is None
    assert tls_ops.aviso() is None
    assert tls_ops.linha_do_arranque() is None


def test_bundle_valido_e_usado_e_anunciado(monkeypatch, ca_de_teste):
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(ca_de_teste))
    assert tls_ops.problema_do_bundle() is None
    assert tls_ops.ca_bundle() is not None
    assert "usando o bundle" in tls_ops.linha_do_arranque()


def test_caminho_inexistente_e_NOMEADO_e_nao_engolido(monkeypatch):
    """O caso relatado, com o caminho real do print."""
    caminho = r"C:\Users\gtrevisan\tools\zscaler-root.pem"
    monkeypatch.setenv("ARBITES_CA_BUNDLE", caminho)
    defeito = tls_ops.problema_do_bundle()
    assert "ARBITES_CA_BUNDLE" in defeito and caminho in defeito
    assert "não existe" in defeito
    assert tls_ops.ca_bundle() is None       # cai no padrão, mas não calado


def test_a_mensagem_nao_manda_declarar_o_que_ja_esta_declarado(monkeypatch):
    """O defeito exato: pedir de novo o que a pessoa acabou de fazer."""
    monkeypatch.setenv("ARBITES_CA_BUNDLE", r"C:\nao\existe.pem")
    texto = tls_ops.explicacao("api.github.com")
    assert "não existe" in texto
    assert "Aponte o bundle" not in texto


def test_pasta_no_lugar_do_arquivo(monkeypatch, tmp_path):
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(tmp_path))
    assert "é uma pasta" in tls_ops.problema_do_bundle()


def test_arquivo_que_nao_e_certificado(monkeypatch, tmp_path):
    """Existir não basta: um `.pem` truncado ou um DER com extensão errada
    passam no teste de existência e só falham na hora da conexão."""
    lixo = tmp_path / "lixo.pem"
    lixo.write_text("isto nao e um certificado\n")
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(lixo))
    assert "não é um bundle" in tls_ops.problema_do_bundle()
    assert tls_ops.ca_bundle() is None


def test_bundle_legivel_mas_sem_a_CA_tem_mensagem_propria(monkeypatch, ca_de_teste):
    """Legível e ainda assim recusado é outro problema: o arquivo está certo,
    a autoridade é que é outra."""
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(ca_de_teste))
    texto = tls_ops.explicacao("api.github.com")
    assert "não contém a CA" in texto
    assert "RAIZ do proxy" in texto     # a dica que resolve na prática


# -- chega sem clicar --------------------------------------------------------

def test_o_problema_aparece_na_lista_sem_ninguem_clicar(ws, monkeypatch):
    monkeypatch.setenv("ARBITES_CA_BUNDLE", r"C:\nao\existe.pem")
    with logged_in_client(ws) as client:
        avisos = client.get("/api/v1/warnings").json()
        codigos = [a["code"] for a in avisos]
        assert "ca_bundle_invalido" in codigos


def test_bundle_bom_nao_polui_a_lista(ws, monkeypatch, ca_de_teste):
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(ca_de_teste))
    with logged_in_client(ws) as client:
        codigos = [a["code"] for a in client.get("/api/v1/warnings").json()]
        assert "ca_bundle_invalido" not in codigos
