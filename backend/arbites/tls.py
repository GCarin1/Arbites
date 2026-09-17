"""Confiança TLS numa rede que inspeciona o tráfego (change 0183).

Em rede corporativa o tráfego HTTPS costuma passar por um proxy que
RE-ASSINA os certificados com uma CA da empresa. O Python não conhece essa
CA — o pacote `certifi` só traz as públicas —, e toda chamada a
`api.github.com` morre com `CERTIFICATE_VERIFY_FAILED: unable to get local
issuer certificate`.

O caminho é apontar o bundle da empresa, nunca desligar a verificação.
Desligar transformaria o proxy em qualquer um: o Arbites manda um PAT do
GitHub nessa conexão, e sem verificar o certificado não há como saber para
quem. Por isso este módulo não tem, e não deve ganhar, um `verify=False`.

As variáveis são as de sempre, na ordem: a específica do Arbites primeiro,
depois as duas que o ecossistema Python já usa e que a máquina corporativa
provavelmente já tem definidas.
"""

from __future__ import annotations

import os
from pathlib import Path

VARIAVEIS = ("ARBITES_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE")


def ca_bundle() -> str | None:
    """O caminho do bundle declarado, se existir em disco.

    Um caminho que não existe é ignorado em silêncio de propósito: cair para
    o bundle padrão dá um erro de TLS compreensível, enquanto passar um
    arquivo inexistente ao httpx dá um `IOError` que não ajuda ninguém.
    """
    for nome in VARIAVEIS:
        valor = (os.environ.get(nome) or "").strip()
        if valor and Path(valor).is_file():
            return valor
    return None


def verify():
    """O que passar em `verify=` do httpx: o bundle da empresa, ou o padrão."""
    return ca_bundle() or True


def declarado() -> str | None:
    """A variável que está valendo — para a mensagem de erro dizer se havia
    bundle configurado ou não."""
    for nome in VARIAVEIS:
        valor = (os.environ.get(nome) or "").strip()
        if valor and Path(valor).is_file():
            return nome
    return None


def e_erro_de_certificado(exc: BaseException) -> bool:
    """O erro é de CONFIANÇA, e não de rede?

    O httpx embrulha o erro de SSL em `ConnectError`, então a distinção só
    aparece no texto — e ela importa: rede fora do ar pede esperar, CA
    desconhecida pede configurar. Tratar as duas igual manda a pessoa
    esperar por algo que nunca vai acontecer sozinho.
    """
    texto = " ".join(str(parte) for parte in _cadeia(exc)).upper()
    return any(marca in texto for marca in (
        "CERTIFICATE_VERIFY_FAILED", "SSLCERTVERIFICATIONERROR",
        "SSL: ", "CERTIFICATE VERIFY FAILED", "SELF SIGNED CERTIFICATE",
    ))


def _cadeia(exc: BaseException) -> list[BaseException]:
    saida, visto = [], set()
    atual: BaseException | None = exc
    while atual is not None and id(atual) not in visto:
        visto.add(id(atual))
        saida.append(atual)
        atual = atual.__cause__ or atual.__context__
    return saida


def explicacao(destino: str) -> str:
    """A mensagem que vai para quem está olhando a tela."""
    atual = declarado()
    if atual:
        return (
            f"o certificado de {destino} não foi aceito mesmo com o bundle de"
            f" {atual}. O arquivo apontado pode não conter a CA que assina"
            " este destino — confirme com quem cuida da rede qual bundle usar."
        )
    return (
        f"o certificado de {destino} não foi reconhecido. Em rede corporativa"
        " o tráfego costuma passar por um proxy que re-assina os certificados"
        " com uma CA da empresa, que o Python não conhece. Aponte o bundle da"
        " sua empresa numa destas variáveis (no `.env` ou no ambiente):"
        f" {', '.join(VARIAVEIS)}."
        " Exemplo: ARBITES_CA_BUNDLE=C:\\\\certs\\\\empresa.pem"
    )
