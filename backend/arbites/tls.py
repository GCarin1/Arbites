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


def apontado() -> tuple[str, str] | None:
    """A primeira variável DECLARADA e o valor dela, use ou não.

    Separado de `ca_bundle()` de propósito: "não declarou" e "declarou e não
    dá para usar" pedem mensagens opostas, e tratá-las igual manda a pessoa
    declarar o que ela acabou de declarar — que foi exatamente o que
    aconteceu (change 0186).
    """
    for nome in VARIAVEIS:
        valor = (os.environ.get(nome) or "").strip()
        if valor:
            return nome, valor
    return None


def problema_do_bundle() -> str | None:
    """Por que o bundle apontado não serve — ou None quando serve.

    Não basta existir: um `.pem` truncado, um DER com extensão errada ou um
    arquivo sem permissão de leitura passam no teste de existência e só
    falham na hora da conexão, com um erro que não aponta para o arquivo.
    """
    atual = apontado()
    if atual is None:
        return None
    nome, valor = atual
    caminho = Path(valor)
    if not caminho.exists():
        return f"{nome} aponta para `{valor}`, que não existe neste computador"
    if not caminho.is_file():
        return f"{nome} aponta para `{valor}`, que é uma pasta, não um arquivo"
    try:
        import ssl

        ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT).load_verify_locations(cafile=valor)
    except (OSError, ssl.SSLError) as exc:
        return (f"{nome} aponta para `{valor}`, que não é um bundle de"
                f" certificados legível ({exc})")
    return None


def ca_bundle() -> str | None:
    """O caminho do bundle declarado, quando dá para usar.

    Um bundle inválido cai para o padrão em vez de estourar na conexão: o
    `IOError` do httpx não diz nada a quem está olhando. O que NÃO pode é
    cair em silêncio — daí `problema_do_bundle()`, que nomeia o motivo.
    """
    atual = apontado()
    if atual is None or problema_do_bundle() is not None:
        return None
    return atual[1]


def verify():
    """O que passar em `verify=` do httpx: o bundle da empresa, ou o padrão."""
    return ca_bundle() or True


def declarado() -> str | None:
    """A variável cujo bundle está EM USO (declarada e utilizável)."""
    atual = apontado()
    if atual is None or problema_do_bundle() is not None:
        return None
    return atual[0]


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
    """A mensagem que vai para quem está olhando a tela.

    Três situações, três mensagens. A pior falha possível aqui é mandar
    declarar uma variável que já está declarada — quem recebe isso conclui,
    com razão, que a ferramenta não está lendo o `.env`.
    """
    defeito = problema_do_bundle()
    if defeito:
        return (
            f"{defeito}. Por isso a verificação de {destino} caiu no bundle"
            " padrão e falhou. Confira o caminho — no Windows, copie-o do"
            " Explorador — e reinicie o Arbites."
        )
    atual = declarado()
    if atual:
        return (
            f"o certificado de {destino} não foi aceito mesmo com o bundle de"
            f" {atual}. O arquivo é legível, mas não contém a CA que assina"
            " este destino — confirme com quem cuida da rede qual bundle usar"
            " (numa rede com Zscaler ou similar, costuma ser o certificado"
            " RAIZ do proxy, não o do site)."
        )
    return (
        f"o certificado de {destino} não foi reconhecido. Em rede corporativa"
        " o tráfego costuma passar por um proxy que re-assina os certificados"
        " com uma CA da empresa, que o Python não conhece. Aponte o bundle da"
        " sua empresa numa destas variáveis (no `.env` ou no ambiente):"
        f" {', '.join(VARIAVEIS)}."
        " Exemplo: ARBITES_CA_BUNDLE=C:\\\\certs\\\\empresa.pem"
    )


def aviso() -> dict[str, object] | None:
    """O bundle quebrado no formato da lista de problemas.

    Aparece sem ninguém clicar em nada: uma configuração que não funciona só
    se revela na primeira chamada externa, e até lá parece que está tudo
    certo (change 0186).
    """
    defeito = problema_do_bundle()
    if not defeito:
        return None
    from datetime import datetime, timezone

    return {
        "source_path": ".env",
        "code": "ca_bundle_invalido",
        "message": (f"{defeito}. Toda chamada externa vai cair no bundle"
                    " padrão, que numa rede que inspeciona TLS falha."),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def linha_do_arranque() -> str | None:
    """Uma linha para o terminal, ou None quando está tudo certo."""
    defeito = problema_do_bundle()
    if defeito:
        return f"ATENÇÃO: {defeito}."
    atual = declarado()
    return f"CA da rede: usando o bundle de {atual}." if atual else None
