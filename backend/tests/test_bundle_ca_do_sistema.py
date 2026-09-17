"""O bundle montado a partir do que a máquina já confia (change 0188).

"O arquivo é legível, mas não contém a CA que assina este destino" é uma
mensagem correta e inútil: ela diz o que está errado e não diz onde achar o
certo. Quem tenta resolver na mão exporta o certificado do SITE, ou o
intermediário no lugar da raiz, ou salva em DER com extensão `.pem` — e
volta para a mesma mensagem.

A CA da empresa já está instalada no Windows; sem ela o navegador não
abriria nada. Estes testes fixam as duas metades do conserto: montar o
bundle a partir dali, e dizer QUEM assinou o certificado apresentado.
"""

from __future__ import annotations

import ssl
import subprocess
import threading

import pytest

from arbites import bundle_ca, diagnostico


@pytest.fixture
def der_de_teste(ca_de_teste):
    return ssl.PEM_cert_to_DER_cert(ca_de_teste.read_text())


def _armazem(monkeypatch, entradas):
    monkeypatch.setattr(ssl, "enum_certificates",
                        lambda nome: entradas.get(nome, []), raising=False)


# --- montagem ---------------------------------------------------------------


def test_o_bundle_junta_as_publicas_com_as_da_maquina(
        tmp_path, monkeypatch, der_de_teste):
    """Só as do Windows daria um bundle que só funciona com o que passa pelo
    proxy — e algum destino sempre escapa dele."""
    _armazem(monkeypatch, {"ROOT": [(der_de_teste, "x509_asn", True)]})

    resumo = bundle_ca.montar(tmp_path / "ca.pem")

    assert resumo["do_sistema"] == 1
    assert resumo["publicos"] > 100  # as raízes públicas continuam lá
    assert resumo["carregados"] == resumo["publicos"] + 1


def test_o_bundle_escrito_carrega_de_verdade(tmp_path, monkeypatch,
                                             der_de_teste):
    """Escrever um arquivo que não abre seria trocar uma falha silenciosa por
    outra: a validação acontece agora, não na primeira chamada."""
    _armazem(monkeypatch, {"ROOT": [(der_de_teste, "x509_asn", True)]})

    destino = tmp_path / "ca.pem"
    bundle_ca.montar(destino)

    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    contexto.load_verify_locations(cafile=str(destino))  # não levanta
    assert "BEGIN CERTIFICATE" in destino.read_text()


def test_certificado_que_nao_autentica_servidor_fica_de_fora(
        tmp_path, monkeypatch, der_de_teste):
    """O armazenamento do Windows guarda CA de assinatura de código e de
    e-mail também; ampliar a confiança além do necessário é o oposto do que
    este comando existe para fazer."""
    so_email = {"1.3.6.1.5.5.7.3.4"}
    _armazem(monkeypatch, {"ROOT": [(der_de_teste, "x509_asn", so_email)]})

    resumo = bundle_ca.montar(tmp_path / "ca.pem")

    assert resumo["do_sistema"] == 0


def test_o_mesmo_certificado_nos_dois_armazens_entra_uma_vez(
        tmp_path, monkeypatch, der_de_teste):
    _armazem(monkeypatch, {
        "ROOT": [(der_de_teste, "x509_asn", True)],
        "CA": [(der_de_teste, "x509_asn", True)],
    })

    resumo = bundle_ca.montar(tmp_path / "ca.pem")

    assert resumo["do_sistema"] == 1


def test_intermediario_do_armazem_ca_tambem_entra(tmp_path, monkeypatch,
                                                  der_de_teste):
    """Há empresa que instala só o intermediário; ignorar o armazém `CA`
    deixaria essa máquina sem conserto."""
    _armazem(monkeypatch, {"CA": [(der_de_teste, "x509_asn", True)]})

    assert bundle_ca.montar(tmp_path / "ca.pem")["do_sistema"] == 1


def test_montar_nao_declara_a_confianca_por_conta_propria(
        tmp_path, monkeypatch, der_de_teste):
    """Quem decide em quem confiar é quem opera a máquina, por escrito. O
    comando escreve um arquivo e mostra a linha; não mexe no ambiente."""
    import os

    _armazem(monkeypatch, {"ROOT": [(der_de_teste, "x509_asn", True)]})
    antes = dict(os.environ)

    bundle_ca.montar(tmp_path / "ca.pem")

    assert dict(os.environ) == antes


# --- o que a tela diz -------------------------------------------------------


def test_fora_do_windows_o_comando_diz_isso_e_aponta_o_caminho(monkeypatch):
    monkeypatch.delattr(ssl, "enum_certificates", raising=False)

    saida = "\n".join(bundle_ca.relatorio("/tmp/nao-sera-escrito.pem"))

    assert "não é Windows" in saida
    assert "ca-certificates.crt" in saida


def test_sem_nenhum_certificado_da_maquina_o_recado_e_outro(tmp_path,
                                                            monkeypatch):
    """Um bundle só com as públicas é exatamente o que já falhava. Chamar
    isso de sucesso mandaria a pessoa de volta para a mesma mensagem."""
    _armazem(monkeypatch, {})

    saida = "\n".join(bundle_ca.relatorio(tmp_path / "ca.pem"))

    assert "NENHUM certificado veio" in saida
    assert "não está instalada" in saida


def test_a_linha_do_env_sai_pronta_e_com_barra_normal(tmp_path, monkeypatch,
                                                      der_de_teste):
    """Barra invertida no `.env` é a armadilha da change 0187; a linha já sai
    do jeito que funciona."""
    _armazem(monkeypatch, {"ROOT": [(der_de_teste, "x509_asn", True)]})

    saida = "\n".join(bundle_ca.relatorio(tmp_path / "ca.pem"))

    linha = next(l for l in saida.splitlines() if "ARBITES_CA_BUNDLE=" in l)
    assert "\\" not in linha


# --- quem assinou -----------------------------------------------------------


@pytest.fixture
def servidor_tls(tmp_path):
    """Um servidor TLS de verdade, com certificado próprio, para olhar."""
    cert = tmp_path / "servidor.pem"
    chave = tmp_path / "servidor.key"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(chave), "-out", str(cert), "-days", "1",
         "-subj", "/CN=localhost/O=Proxy-Da-Empresa"],
        check=True, capture_output=True,
    )
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto.load_cert_chain(str(cert), str(chave))

    import socket

    ouvinte = socket.socket()
    ouvinte.bind(("127.0.0.1", 0))
    ouvinte.listen(1)
    porta = ouvinte.getsockname()[1]

    def atender():
        try:
            cru, _ = ouvinte.accept()
            with contexto.wrap_socket(cru, server_side=True):
                pass
        except OSError:
            pass

    thread = threading.Thread(target=atender, daemon=True)
    thread.start()
    yield porta
    ouvinte.close()


def test_o_emissor_do_certificado_apresentado_e_dito_por_extenso(servidor_tls):
    """"Não contém a CA que assina este destino" sem dizer QUAL CA é deixa a
    pessoa procurando no escuro — foi exatamente o que aconteceu."""
    pytest.importorskip("cryptography")

    saida = "\n".join(diagnostico.quem_assinou("127.0.0.1", servidor_tls))

    assert "EMISSOR:" in saida
    assert "Proxy-Da-Empresa" in saida


def test_destino_inalcancavel_nao_derruba_o_diagnostico():
    """O diagnóstico é o último lugar onde uma exceção pode subir: quem o
    roda já está sem saída."""
    saida = "\n".join(diagnostico.quem_assinou("127.0.0.1", 1))

    assert "nao deu para olhar" in saida
