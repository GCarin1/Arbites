"""O comando que mostra o que o PROCESSO enxerga (change 0187).

Quatro rodadas de depuração por captura de tela custaram quatro ciclos: o
`.env` da pessoa estava certo e a variável não chegava ao processo. Estes
testes fixam as três diferenças que um print não mostra — o diretório, a
linha descartada em silêncio e o ambiente que vence o arquivo — e a regra
inegociável: um relatório feito para ser colado num chat não imprime senha
nem token.
"""

from __future__ import annotations

import os

import pytest

from arbites import diagnostico, envfile


# --- o BOM que apagava a primeira linha ------------------------------------


def test_bom_do_bloco_de_notas_nao_come_a_primeira_chave(tmp_path, monkeypatch):
    """Gravado pelo Bloco de Notas, o `.env` começa com BOM — e a primeira
    chave virava `\ufeffARBITES_...`, descartada SEM UMA PALAVRA."""
    (tmp_path / ".env").write_bytes(
        "\ufeffARBITES_CA_BUNDLE=/tmp/x.pem\nOUTRA=2\n".encode("utf-8")
    )
    monkeypatch.delenv("ARBITES_CA_BUNDLE", raising=False)
    monkeypatch.delenv("OUTRA", raising=False)

    aplicadas = envfile.carregar(tmp_path)

    assert "ARBITES_CA_BUNDLE" in aplicadas
    assert os.environ["ARBITES_CA_BUNDLE"] == "/tmp/x.pem"


def test_linha_descartada_e_nomeada_com_o_numero_e_o_motivo():
    achados = envfile.descartadas("A=1\nexport B=2\nsó texto\n")
    numeros = {numero: motivo for numero, motivo, _ in achados}

    assert 2 in numeros and "export" in numeros[2]
    assert 3 in numeros and "`=`" in numeros[3]


def test_linha_descartada_nao_carrega_o_valor_junto():
    """O motivo vai para a tela; o valor NÃO — este arquivo tem senha."""
    achados = envfile.descartadas("export ARBITES_ADMIN_PASSWORD=SenhaSuperSecreta\n")

    assert achados
    assert all("SenhaSuperSecreta" not in trecho for _, _, trecho in achados)


# --- as pistas que o `repr()` mostra e ninguém lê ---------------------------


@pytest.mark.parametrize("valor,marca", [
    ("C:\\\\certs\\\\ca.pem", "DUPLICADAS"),
    ("'C:/certs/ca.pem'", "aspas"),
    (" /certs/ca.pem", "espaço"),
    ("%USERPROFILE%/ca.pem", "expande"),
])
def test_valor_suspeito_e_explicado_por_extenso(valor, marca):
    pista = envfile.pista_do_valor(valor)

    assert pista and marca in pista


def test_caminho_normal_nao_inventa_suspeita():
    assert envfile.pista_do_valor("C:/certs/ca.pem") is None


# --- o .env é o do DIRETÓRIO ATUAL -----------------------------------------


def test_sem_env_nenhum_o_relatorio_diz_de_onde_procurou(tmp_path):
    saida = "\n".join(diagnostico.secao_env(tmp_path))

    assert str(tmp_path) in saida
    assert "NAO ENCONTRADO" in saida


def test_env_da_pasta_de_cima_e_encontrado_e_o_caminho_e_dito(tmp_path):
    """`cd backend && python -m arbites serve` é o comando documentado, e o
    `.env` de todo mundo está um nível acima: sem subir, o arquivo existe,
    está certo, e nunca é lido."""
    (tmp_path / ".env").write_text("ARBITES_CA_BUNDLE=/x.pem\n")
    sub = tmp_path / "backend"
    sub.mkdir()

    saida = "\n".join(diagnostico.secao_env(sub))

    assert f"usando: {tmp_path / '.env'}" in saida
    assert "pasta ACIMA" in saida


def test_a_busca_nao_sobe_alem_do_limite(tmp_path):
    """Subir sem limite sequestraria um `.env` da pasta pessoal de alguém —
    um arquivo que quem rodou o comando nem lembra que existe."""
    from arbites import envfile

    fundo = tmp_path.joinpath(*[f"n{i}" for i in range(envfile.NIVEIS + 2)])
    fundo.mkdir(parents=True)
    (tmp_path / ".env").write_text("A=1\n")

    assert envfile.localizar(fundo) is None


def test_ambiente_que_venceu_o_arquivo_aparece(tmp_path, monkeypatch):
    """A precedência é de propósito (o ambiente ganha) e invisível: o arquivo
    mostra um valor, o processo usa outro."""
    (tmp_path / ".env").write_text("ARBITES_CA_BUNDLE=/do/arquivo.pem\n")
    monkeypatch.setenv("ARBITES_CA_BUNDLE", "/do/ambiente.pem")

    saida = "\n".join(diagnostico.secao_env(tmp_path))

    assert "AMBIENTE venceu" in saida


# --- CA ---------------------------------------------------------------------


def test_bundle_quebrado_mascara_a_variavel_seguinte_e_isso_e_dito(
        tmp_path, monkeypatch, ca_de_teste):
    """A primeira DECLARADA vence, mesmo quebrada. Quem declarou a segunda
    certa não tem como saber que ela nunca foi consultada."""
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(tmp_path / "nao-existe.pem"))
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(ca_de_teste))
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)

    saida = "\n".join(diagnostico.secao_ca())

    assert "PROBLEMA" in saida
    assert "REQUESTS_CA_BUNDLE" in saida.split("->", 1)[1]


def test_bundle_bom_e_contado_em_certificados(monkeypatch, ca_de_teste):
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(ca_de_teste))
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)

    saida = "\n".join(diagnostico.secao_ca())

    assert "carrega como bundle: sim (1 certificado(s))" in saida
    assert "em uso agora: ARBITES_CA_BUNDLE" in saida


def test_nenhuma_variavel_declarada_e_dito_sem_rodeio(monkeypatch):
    for nome in ("ARBITES_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        monkeypatch.delenv(nome, raising=False)

    saida = "\n".join(diagnostico.secao_ca())

    assert "NENHUMA das três" in saida


# --- rede -------------------------------------------------------------------


class _ClienteFalso:
    def __init__(self, erro=None, status=200, **kwargs):
        self.erro, self.status, self.kwargs = erro, status, kwargs

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, headers=None):
        if self.erro:
            raise self.erro
        return type("R", (), {"status_code": self.status})()


def _com_cliente(monkeypatch, **kwargs):
    import httpx

    capturado = {}

    def fabrica(**k):
        capturado.update(k)
        return _ClienteFalso(**kwargs)

    monkeypatch.setattr(httpx, "Client", fabrica)
    return capturado


def test_erro_de_certificado_vira_explicacao_e_nao_traceback(monkeypatch):
    import httpx

    for nome in ("ARBITES_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        monkeypatch.delenv(nome, raising=False)
    erro = httpx.ConnectError(
        "[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate")
    _com_cliente(monkeypatch, erro=erro)

    saida = "\n".join(diagnostico.secao_rede("https://api.github.com"))

    assert "FALHA DE CERTIFICADO" in saida
    assert "proxy que re-assina" in saida


def test_a_prova_de_rede_usa_o_bundle_declarado(monkeypatch, ca_de_teste):
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(ca_de_teste))
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    capturado = _com_cliente(monkeypatch)

    diagnostico.secao_rede("https://api.github.com")

    assert capturado["verify"] == str(ca_de_teste)
    assert capturado["verify"] is not False  # nunca, em hipótese nenhuma


def test_pat_recusado_e_separado_de_rede_fora(monkeypatch):
    _com_cliente(monkeypatch, status=401)

    saida = "\n".join(diagnostico.secao_rede("https://api.github.com",
                                             token="ghp_qualquer"))

    assert "PAT foi RECUSADO" in saida
    assert "ghp_qualquer" not in saida


def test_chamada_anonima_vem_antes_da_autenticada(monkeypatch):
    """Sem separar as duas, "a rede não passa" e "o PAT não serve" chegam
    como o mesmo 500 na tela."""
    _com_cliente(monkeypatch, status=200)

    saida = "\n".join(diagnostico.secao_rede("https://api.github.com",
                                             token="ghp_x"))

    assert saida.index("anonimo:") < saida.index("com o PAT:")


# --- segredo nunca sai ------------------------------------------------------


def test_relatorio_inteiro_nao_imprime_senha_nem_token(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "ARBITES_ADMIN_PASSWORD=SenhaQueNaoPodeVazar\n"
        "ARBITES_GITHUB_TOKEN=ghp_TokenQueNaoPodeVazar\n"
    )
    monkeypatch.setenv("ARBITES_GITHUB_TOKEN", "ghp_TokenQueNaoPodeVazar")
    monkeypatch.setenv("ARBITES_ADMIN_PASSWORD", "SenhaQueNaoPodeVazar")

    saida = diagnostico.como_texto(str(tmp_path / "ws"), diretorio=tmp_path,
                                   rede=False)

    assert "SenhaQueNaoPodeVazar" not in saida
    assert "ghp_TokenQueNaoPodeVazar" not in saida
    # ... mas as CHAVES aparecem: é o que permite conferir o que chegou.
    assert "ARBITES_ADMIN_PASSWORD" in saida


def test_credencial_e_descrita_por_tamanho_e_origem(monkeypatch):
    monkeypatch.setenv("ARBITES_GITHUB_TOKEN", "ghp_1234567890")

    linhas, token = diagnostico.secao_credencial()

    assert token == "ghp_1234567890"
    assert "origem: env" in "\n".join(linhas)
    assert "ghp_1234567890" not in "\n".join(linhas)


def test_token_com_espaco_nas_pontas_e_denunciado(monkeypatch):
    """Colar o PAT de um e-mail traz espaço junto, e o GitHub responde 401
    sem dizer por quê."""
    monkeypatch.setenv("ARBITES_GITHUB_TOKEN", "ghp_valido ")

    saida = "\n".join(diagnostico.secao_credencial()[0])

    assert "espaço ou quebra de linha" in saida
