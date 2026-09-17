"""Montar o bundle de CA a partir do que a MÁQUINA já confia (change 0188).

## O problema que isto resolve

Numa rede com Zscaler (ou qualquer proxy que re-assine TLS), a CA da empresa
já está instalada no Windows — senão o Chrome não abriria site nenhum. O
Python é que não a enxerga: ele traz o `certifi`, que só tem as CAs públicas.

Quem tenta resolver isso na mão erra quase sempre, e erra em silêncio: exporta
o certificado do SITE em vez do da CA, ou o intermediário em vez da raiz, ou
exporta em DER com extensão `.pem`. O resultado é um arquivo legível que não
contém a CA que assina o destino — a mensagem que não diz o que fazer.

## Por que um COMANDO, e não leitura automática

Ler o armazenamento do Windows sozinho, na hora da conexão, seria o programa
decidindo em quem confiar sem perguntar. Essa decisão é de quem opera a
máquina, e ela precisa ser visível: um dia alguém instala uma CA indevida no
Windows e o Arbites passaria a aceitá-la sem que ninguém tivesse dito nada.

Então o desenho é: o comando ESCREVE um arquivo, diz quantos certificados
vieram de onde, e imprime a linha que a pessoa precisa colar no `.env`. Quem
confia é ela, por escrito. O programa só junta o que já estava lá.

## O que entra no arquivo

As raízes públicas do `certifi` E as do armazenamento do Windows. Só as do
Windows daria um bundle que só funciona com o que passa pelo proxy — e algum
destino sempre escapa dele.
"""

from __future__ import annotations

import ssl
from pathlib import Path

# Só certificado habilitado para autenticar SERVIDOR entra. O armazenamento do
# Windows guarda também CAs de assinatura de código e de e-mail, e ampliar a
# confiança para além do necessário é o oposto do objetivo aqui.
OID_SERVIDOR = "1.3.6.1.5.5.7.3.1"

# `ROOT` são as raízes confiáveis; `CA` guarda os intermediários. O Zscaler
# costuma instalar a raiz em `ROOT`, mas há empresa que só põe o intermediário.
ARMAZENS = ("ROOT", "CA")


def disponivel() -> bool:
    """Se esta máquina tem armazenamento de certificados legível pelo Python.

    `ssl.enum_certificates` só existe no Windows — é justamente onde o
    problema acontece.
    """
    return hasattr(ssl, "enum_certificates")


def do_sistema() -> list[str]:
    """Os certificados do Windows habilitados para servidor, em PEM."""
    if not disponivel():
        return []
    vistos: set[bytes] = set()
    saida: list[str] = []
    for armazem in ARMAZENS:
        try:
            entradas = ssl.enum_certificates(armazem)
        except Exception:  # noqa: BLE001 — armazém ausente não é acidente
            continue
        for der, codificacao, confianca in entradas:
            if codificacao != "x509_asn" or der in vistos:
                continue
            # `True` = confiança para todos os usos; um conjunto = só para os
            # OIDs listados.
            if confianca is not True and OID_SERVIDOR not in (confianca or ()):
                continue
            vistos.add(der)
            saida.append(ssl.DER_cert_to_PEM_cert(der))
    return saida


def publicos() -> list[str]:
    """As raízes públicas do `certifi` — o que o Python já usaria."""
    import certifi

    texto = Path(certifi.where()).read_text(encoding="utf-8")
    partes = texto.split("-----END CERTIFICATE-----")
    return [p.strip() + "\n-----END CERTIFICATE-----\n"
            for p in partes if "-----BEGIN CERTIFICATE-----" in p]


def montar(destino: str | Path) -> dict[str, object]:
    """Escreve o bundle e devolve o que foi escrito, para dizer na tela.

    Não toca em variável de ambiente nem em configuração: quem declara o
    bundle é a pessoa, com o caminho na mão.
    """
    caminho = Path(destino)
    do_windows = do_sistema()
    publicas = publicos()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("".join(publicas + do_windows), encoding="ascii")
    # Recarrega o que acabou de escrever: um bundle que não abre não serve, e
    # descobrir isso agora é melhor que descobrir na primeira chamada.
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    contexto.load_verify_locations(cafile=str(caminho))
    return {
        "caminho": str(caminho.resolve()),
        "do_sistema": len(do_windows),
        "publicos": len(publicas),
        "carregados": len(contexto.get_ca_certs()),
    }


def relatorio(destino: str | Path) -> list[str]:
    if not disponivel():
        return [
            "Este comando lê o armazenamento de certificados do WINDOWS, e"
            " esta máquina não é Windows.",
            "Em Linux/macOS o bundle da empresa costuma já estar em"
            " /etc/ssl/certs/ca-certificates.crt (Debian/Ubuntu) ou"
            " /etc/pki/tls/certs/ca-bundle.crt (RHEL/Fedora).",
        ]
    resumo = montar(destino)
    if not resumo["do_sistema"]:
        return [
            f"Escrito {resumo['caminho']}, mas NENHUM certificado veio do"
            " armazenamento do Windows — só as raízes públicas.",
            "Isso quer dizer que a CA da empresa não está instalada para este"
            " usuário. Rode o comando com a conta que usa o navegador, ou"
            " peça o certificado raiz a quem cuida da rede.",
        ]
    return [
        f"Bundle escrito em {resumo['caminho']}",
        f"  {resumo['publicos']} raízes públicas (certifi)",
        f"  {resumo['do_sistema']} certificados do Windows (inclui a CA da"
        " sua empresa, que é o que faltava)",
        f"  {resumo['carregados']} carregam como bundle",
        "",
        "Agora declare este arquivo no `.env`, na raiz do projeto:",
        f"  ARBITES_CA_BUNDLE={resumo['caminho']}".replace("\\", "/"),
        "",
        "E suba o Arbites de novo. O arranque vai dizer qual bundle está em uso.",
    ]
