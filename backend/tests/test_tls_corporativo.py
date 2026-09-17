"""Rede corporativa que re-assina o TLS (change 0183).

O proxy da empresa re-emite os certificados com uma CA própria; o Python só
conhece as públicas do `certifi`. Toda chamada a `api.github.com` morria com
`CERTIFICATE_VERIFY_FAILED` — e, pior, o erro subia cru: quem clicou em
"Buscar execuções" recebia 500 com uma parede de traceback no terminal, em
vez da única coisa útil (apontar o bundle da empresa).
"""

import ssl

import httpx
import pytest
from conftest import logged_in_client

from arbites import tls as tls_ops
from arbites.ci import CIError, HttpxGitHub


class TokensFalso:
    def get(self):
        return "ghp_falso"

    def available(self):
        return True

    def source(self):
        return "env"


def _erro_de_certificado() -> httpx.ConnectError:
    """O que o httpx levanta quando a CA não é reconhecida."""
    causa = ssl.SSLCertVerificationError(
        "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:"
        " unable to get local issuer certificate (_ssl.c:1000)")
    erro = httpx.ConnectError("certificate verify failed")
    erro.__cause__ = causa
    return erro


# -- o bundle ----------------------------------------------------------------

def test_sem_bundle_declarado_usa_o_padrao(monkeypatch):
    for nome in tls_ops.VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)
    assert tls_ops.ca_bundle() is None
    assert tls_ops.verify() is True


@pytest.mark.parametrize("variavel", tls_ops.VARIAVEIS)
def test_qualquer_uma_das_variaveis_serve(monkeypatch, ca_de_teste, variavel):
    """As duas últimas são as que o ecossistema Python já usa: a máquina
    corporativa provavelmente já as tem definidas."""
    for nome in tls_ops.VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)
    bundle = ca_de_teste
    monkeypatch.setenv(variavel, str(bundle))
    assert tls_ops.ca_bundle() == str(bundle)
    assert tls_ops.verify() == str(bundle)


def test_caminho_inexistente_e_ignorado(monkeypatch, tmp_path):
    """Passar um arquivo que não existe ao httpx dá um IOError que não ajuda
    ninguém; cair no bundle padrão dá um erro de TLS compreensível."""
    for nome in tls_ops.VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(tmp_path / "nao-existe.pem"))
    assert tls_ops.verify() is True


def test_a_ordem_e_a_especifica_primeiro(monkeypatch, ca_de_teste, tmp_path):
    outro = tmp_path / "requests.pem"
    outro.write_bytes(ca_de_teste.read_bytes())
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(ca_de_teste))
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(outro))
    assert tls_ops.ca_bundle() == str(ca_de_teste)


# -- distinguir confiança de rede --------------------------------------------

def test_erro_de_certificado_e_reconhecido():
    assert tls_ops.e_erro_de_certificado(_erro_de_certificado()) is True


def test_queda_de_rede_nao_e_confundida_com_certificado():
    """Certificado e rede pedem ações OPOSTAS — configurar e esperar. Tratar
    as duas igual manda a pessoa esperar por algo que nunca acontece."""
    assert tls_ops.e_erro_de_certificado(
        httpx.ConnectError("[Errno 111] Connection refused")) is False
    assert tls_ops.e_erro_de_certificado(httpx.ReadTimeout("tempo")) is False


def test_a_mensagem_muda_conforme_ha_ou_nao_bundle(monkeypatch, ca_de_teste):
    for nome in tls_ops.VARIAVEIS:
        monkeypatch.delenv(nome, raising=False)
    sem = tls_ops.explicacao("api.github.com")
    assert "ARBITES_CA_BUNDLE" in sem and "proxy" in sem
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(ca_de_teste))
    com = tls_ops.explicacao("api.github.com")
    assert "mesmo com o bundle" in com


# -- o cliente do GitHub -----------------------------------------------------

def test_certificado_recusado_vira_erro_explicado_e_nao_500(monkeypatch):
    """O defeito relatado: 500 com traceback em vez do que fazer."""
    monkeypatch.setattr(
        httpx, "request",
        lambda *a, **k: (_ for _ in ()).throw(_erro_de_certificado()))
    cliente = HttpxGitHub(TokensFalso())
    with pytest.raises(CIError) as exc:
        cliente.list_workflow_runs("org/repo", None, 1, 10)
    assert exc.value.code == "tls_untrusted"
    assert exc.value.status == 502
    assert "ARBITES_CA_BUNDLE" in str(exc.value) or "bundle" in str(exc.value)


def test_rede_fora_do_ar_tem_codigo_proprio(monkeypatch):
    monkeypatch.setattr(
        httpx, "request",
        lambda *a, **k: (_ for _ in ()).throw(
            httpx.ConnectError("[Errno 111] Connection refused")))
    cliente = HttpxGitHub(TokensFalso())
    with pytest.raises(CIError) as exc:
        cliente.list_workflow_runs("org/repo", None, 1, 10)
    assert exc.value.code == "unreachable"


def test_o_bundle_declarado_chega_no_httpx(monkeypatch, ca_de_teste):
    bundle = ca_de_teste
    monkeypatch.setenv("ARBITES_CA_BUNDLE", str(bundle))
    vistos = {}

    def espiao(method, url, **kwargs):
        vistos.update(kwargs)
        return httpx.Response(200, json={"workflow_runs": []},
                              request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", espiao)
    HttpxGitHub(TokensFalso()).list_workflow_runs("org/repo", None, 1, 10)
    assert vistos["verify"] == str(bundle)


def test_a_ingestao_registra_o_erro_e_nao_estoura(ws, monkeypatch):
    """A marca d'água é o disco: recusar limpo não perde nada, e a próxima
    tentativa recomeça de onde parou."""
    import yaml
    from arbites.ci_ingest import CIIngestor
    from arbites.indexer import connect

    cfg = ws.config()
    cfg["observability"] = {"sources": [{"provider": "github", "repo": "org/repo"}]}
    ws.config_path.write_text(
        yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(
        httpx, "request",
        lambda *a, **k: (_ for _ in ()).throw(_erro_de_certificado()))

    resumo = CIIngestor(ws, connect(ws), HttpxGitHub(TokensFalso())).ingerir()
    assert resumo["ingested"] == []
    assert resumo["errors"][0]["code"] == "tls_untrusted"
    assert resumo["stopped"] == "tls_untrusted"


def test_a_rota_de_ingestao_responde_o_erro_em_vez_de_500(ws, monkeypatch):
    import yaml

    cfg = ws.config()
    cfg["observability"] = {"sources": [{"provider": "github", "repo": "org/repo"}]}
    ws.config_path.write_text(
        yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(
        httpx, "request",
        lambda *a, **k: (_ for _ in ()).throw(_erro_de_certificado()))
    monkeypatch.setenv("ARBITES_GITHUB_TOKEN", "ghp_falso")

    with logged_in_client(ws) as client:
        r = client.post("/api/v1/ci/ingest")
        assert r.status_code == 200, r.text
        corpo = r.json()
        assert corpo["errors"][0]["code"] == "tls_untrusted"
        assert "bundle" in corpo["errors"][0]["message"]
