"""O que ESTE processo enxerga — o comando que encerra o adivinha-print.

## Por que existe

A configuração de rede corporativa falhou quatro rodadas seguidas, e todas
as quatro foram depuradas por captura de tela: eu olhava o `.env` da pessoa
e deduzia o que o Python leria dali. Deduzir errado é barato para mim e caro
para quem está do outro lado — cada palpite custa um ciclo inteiro.

O defeito, nessas quatro rodadas, nunca esteve no que o arquivo dizia: esteve
na DIFERENÇA entre o arquivo e o que chegou ao processo. Três diferenças
possíveis, todas invisíveis num print:

- o `.env` lido é o do **diretório atual**, não o que está ao lado do código;
- uma linha pode ser descartada em silêncio (BOM, `export`, chave com ponto);
- a variável já existia no ambiente e **ganha** do arquivo (por desenho).

Este módulo não deduz nada: imprime o que `os.environ` tem, com `repr()` —
para aspas sobrando, espaço no fim e barra duplicada aparecerem —, abre os
arquivos apontados e faz uma conexão TLS de verdade.

## O que ele nunca imprime

Valor de token e de senha. O `.env` tem os dois; um diagnóstico serve para
ser colado num chat, e é assim que segredo vaza. Chaves sim, valores não —
exceto os caminhos de bundle de CA, que são o objeto do exame e não são
segredo.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# `pista_do_valor` mora em `envfile` porque a mensagem de TLS na TELA também
# precisa dela — e `tls` não pode importar este módulo sem ciclo.
from .envfile import pista_do_valor

# Segredo é pelo NOME, não pelo conteúdo: adivinhar por heurística erra para
# os dois lados, e errar para o lado de imprimir é irreversível.
SEGREDOS = ("TOKEN", "PASSWORD", "SECRET", "KEY", "PAT")

DESTINO = "https://api.github.com"


def e_segredo(chave: str) -> bool:
    return any(marca in chave.upper() for marca in SEGREDOS)


# ---------------------------------------------------------------------------
# .env


def secao_env(diretorio: str | os.PathLike[str] | None = None) -> list[str]:
    from . import envfile

    base = Path(diretorio or Path.cwd()).resolve()
    caminho = envfile.localizar(base)
    linhas = [f"[.env]  busca a partir de: {base}"
              f" (sobe ate {envfile.NIVEIS} niveis)"]
    if caminho is None:
        linhas.append(
            "  NAO ENCONTRADO. A busca comeca no diretorio ONDE VOCE RODOU o"
            " comando. Rode a partir da pasta do projeto, ou defina as"
            " variaveis direto no ambiente."
        )
        return linhas
    linhas.append(f"  usando: {caminho}")
    if caminho.parent != base:
        linhas.append(f"  (veio de uma pasta ACIMA — {caminho.parent})")

    try:
        texto = caminho.read_text(encoding="utf-8-sig")
    except OSError as exc:
        linhas.append(f"  existe, mas não abre: {exc}")
        return linhas

    do_arquivo = envfile.parse(texto)
    linhas.append(f"  existe; {len(do_arquivo)} chave(s) reconhecida(s):"
                  f" {', '.join(sorted(do_arquivo)) or '(nenhuma)'}")
    for numero, motivo, trecho in envfile.descartadas(texto):
        linhas.append(f"  linha {numero} DESCARTADA ({motivo}): {trecho}")
    for chave in sorted(do_arquivo):
        no_ambiente = os.environ.get(chave)
        if no_ambiente is None:
            linhas.append(f"  {chave}: no arquivo, mas NAO chegou ao ambiente"
                          " deste processo")
        elif no_ambiente != do_arquivo[chave]:
            linhas.append(f"  {chave}: o AMBIENTE venceu o arquivo (quem"
                          " exportou a variável na mão quis aquele valor)")
    return linhas


# ---------------------------------------------------------------------------
# CA


def secao_ca() -> list[str]:
    from . import tls as tls_ops

    linhas = ["", "[CA / TLS]"]
    algum = False
    for nome in tls_ops.VARIAVEIS:
        bruto = os.environ.get(nome)
        if bruto is None:
            linhas.append(f"  {nome}: nao definida")
            continue
        algum = True
        # O caminho do bundle não é segredo — é justamente o que se examina.
        linhas.append(f"  {nome} = {bruto!r}")
        pista = pista_do_valor(bruto)
        if pista:
            linhas.append(f"    ATENCAO: {pista}")
        caminho = Path(bruto.strip())
        linhas.append(f"    existe: {caminho.exists()}  "
                      f"arquivo: {caminho.is_file()}")
        if caminho.is_file():
            linhas.append(f"    carrega como bundle: {_carrega(bruto.strip())}")
    if not algum:
        linhas.append("  NENHUMA das três está definida neste processo —"
                      " é por isso que a tela pede para declarar.")
    em_uso = tls_ops.declarado()
    linhas.append(f"  em uso agora: {em_uso or 'bundle padrao (certifi)'}")
    defeito = tls_ops.problema_do_bundle()
    if defeito:
        linhas.append(f"  PROBLEMA: {defeito}")
        # A ordem das variáveis é fixa e a primeira DECLARADA vence, mesmo
        # quebrada. Quem tem duas definidas — uma errada e uma certa — vê a
        # certa no arquivo e não entende por que nada mudou.
        apontada = tls_ops.apontado()
        sobrando = [n for n in tls_ops.VARIAVEIS
                    if apontada and n != apontada[0]
                    and (os.environ.get(n) or "").strip()]
        if sobrando:
            linhas.append(
                f"  -> {apontada[0]} vem PRIMEIRO na ordem e, quebrada, nao"
                f" deixa {', '.join(sobrando)} ser usada. Corrija-a ou"
                " apague-a."
            )
    return linhas


def _carrega(caminho: str) -> str:
    import ssl

    try:
        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        contexto.load_verify_locations(cafile=caminho)
    except (OSError, ssl.SSLError) as exc:
        return f"NAO ({exc})"
    quantos = len(contexto.get_ca_certs())
    return f"sim ({quantos} certificado(s))"


# ---------------------------------------------------------------------------
# Rede


def secao_rede(destino: str = DESTINO, token: str | None = None) -> list[str]:
    """Uma conexão de verdade — o único juiz que vale.

    Sem token a chamada é anônima de propósito: separa "a rede/TLS não
    passa" de "o PAT não serve", que na tela chegam como o mesmo 500.
    """
    from . import tls as tls_ops

    linhas = ["", f"[rede] GET {destino}/rate_limit"]
    proxy = next((os.environ[n] for n in ("HTTPS_PROXY", "https_proxy")
                  if os.environ.get(n)), None)
    linhas.append(f"  proxy do ambiente: {proxy or 'nenhum'}")
    try:
        import httpx
    except ImportError:  # pragma: no cover - httpx é dependência do projeto
        linhas.append("  httpx não instalado neste interpretador.")
        return linhas

    def _chamar(cabecalhos: dict[str, str]) -> tuple[str, bool]:
        try:
            with httpx.Client(verify=tls_ops.verify(), timeout=15.0) as cliente:
                resp = cliente.get(f"{destino}/rate_limit", headers=cabecalhos)
            return f"HTTP {resp.status_code}", resp.status_code < 400
        except Exception as exc:  # noqa: BLE001 — o diagnóstico é o relatório
            if tls_ops.e_erro_de_certificado(exc):
                return f"FALHA DE CERTIFICADO: {exc}", False
            return f"FALHA DE REDE: {type(exc).__name__}: {exc}", False

    resultado, ok = _chamar({})
    linhas.append(f"  anonimo: {resultado}")
    if not ok and "CERTIFICADO" in resultado:
        linhas.append(f"  -> {tls_ops.explicacao(destino)}")
        return linhas

    if token:
        resultado, ok_pat = _chamar({"Authorization": f"Bearer {token}"})
        linhas.append(f"  com o PAT: {resultado}")
        if not ok_pat and resultado.startswith("HTTP 401"):
            linhas.append("  -> o PAT foi RECUSADO (expirado, revogado, ou"
                          " colado com espaço/quebra de linha).")
    else:
        linhas.append("  com o PAT: nao ha credencial configurada")
    return linhas


# ---------------------------------------------------------------------------
# Workspace


def secao_workspace(workspace: str) -> list[str]:
    from .workspace import Workspace

    ws = Workspace(workspace)
    linhas = ["", f"[workspace] {ws.root}"]
    if not Path(ws.root).is_dir():
        linhas.append("  esta pasta NAO EXISTE — o Arbites que você usa"
                      " aponta para outra. Rode este comando com o mesmo"
                      " `--workspace` do `serve`.")
        return linhas
    try:
        config = ws.config()
    except FileNotFoundError:
        linhas.append("  sem `arbites.yaml` aqui: a pasta existe mas nao e um"
                      " workspace do Arbites.")
        return linhas
    except Exception as exc:  # noqa: BLE001
        linhas.append(f"  arbites.yaml nao carrega: {exc}")
        return linhas
    observ = config.get("observability") or {}
    fontes = [f for f in (observ.get("sources") or []) if f.get("repo")]
    if not fontes:
        linhas.append("  observability.sources: VAZIO — a busca não tem onde"
                      " procurar, e é por isso que ela não traz nada.")
    for fonte in fontes:
        linhas.append(
            f"  fonte: {fonte.get('repo')}"
            f"  workflow={fonte.get('workflow') or '(todos)'}"
            f"  artifact={fonte.get('artifact') or '(padrao)'}"
        )
    return linhas


def secao_credencial() -> tuple[list[str], str | None]:
    from .ci import ENV_TOKEN, TokenStore

    cofre = TokenStore()
    token = cofre.get()
    origem = cofre.source()
    linhas = ["", "[credencial GitHub]"]
    if token:
        # Comprimento e origem bastam para reconhecer "colei errado"; o valor
        # não sai daqui nunca.
        linhas.append(f"  configurada (origem: {origem},"
                      f" {len(token)} caracteres)")
        # O bruto do ambiente, não o que `TokenStore.get()` devolve: ele já
        # apara as pontas, e é justamente a ponta aparada que se quer ver.
        bruto = os.environ.get(ENV_TOKEN) or ""
        if (bruto and bruto != bruto.strip()) or token != token.strip():
            linhas.append("  ATENCAO: o token tem espaço ou quebra de linha"
                          " nas pontas.")
    else:
        linhas.append(f"  nenhuma. Defina {ENV_TOKEN} no ambiente, ou"
                      " guarde o PAT pela tela de Automação.")
    return linhas, token


# ---------------------------------------------------------------------------


def relatorio(workspace: str, diretorio: str | os.PathLike[str] | None = None,
              destino: str = DESTINO, rede: bool = True) -> list[str]:
    from . import versao as versao_ops

    linhas: list[str] = [versao_ops.linha(), f"python: {_python()}", ""]
    linhas += secao_env(diretorio)
    linhas += secao_ca()
    credencial, token = secao_credencial()
    linhas += credencial
    if rede:
        linhas += secao_rede(destino, token)
    else:
        linhas += ["", "[rede] pulado (--sem-rede)"]
    linhas += secao_workspace(workspace)
    return linhas


def _python() -> str:
    import sys

    return f"{sys.version.split()[0]} em {sys.executable}"


def como_texto(*args: Any, **kwargs: Any) -> str:
    return "\n".join(relatorio(*args, **kwargs))
