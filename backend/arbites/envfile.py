"""Leitura do `.env` do processo (change 0165).

## Por que isto faltava, e por que doeu

O `docker-compose.yml` lê o `.env` — isso é recurso do **Compose**, não do
Arbites. Quem sobe em container vê as variáveis chegarem e conclui, com toda a
razão, que o produto lê o arquivo. Fora do container, `python -m arbites serve`
não lia nada: `ARBITES_ADMIN_EMAIL` e `ARBITES_ADMIN_PASSWORD` chegavam
vazias, `bootstrap_admin` não criava conta nenhuma **em silêncio**, e a pessoa
passava a tentar entrar numa conta que nunca existiu — até o bloqueio por
tentativas.

Dois sintomas, uma causa. É o tipo de defeito que não aparece em teste de API
porque o teste define o ambiente na mão.

## A regra de precedência, e por que é essa

**O ambiente do processo GANHA do arquivo.** Quem exportou a variável na mão
quis aquele valor agora; um `.env` esquecido no diretório não pode vencê-la em
silêncio. É a mesma regra que o Compose usa, e a mesma da credencial de CI
(ADR 0017).

## Sobre segredo em arquivo

A ADR 0008 rejeitou "token em arquivo de config" porque o **workspace** é
versionável e compartilhável. O `.env` não é o workspace: ele está no
`.gitignore` do repositório e não viaja com os dados. E, na prática, em
container o token JÁ vinha do `.env` — pelas mãos do Compose. Ler o mesmo
arquivo fora do container é consistência, não um risco novo.
"""

from __future__ import annotations

import os
from pathlib import Path

NOME = ".env"


def parse(texto: str) -> dict[str, str]:
    """Formato mínimo e previsível: `CHAVE=valor`, `#` comenta, aspas saem.

    Não interpreta `export`, substituição de variável nem várias linhas: um
    `.env` que se comporta como shell é um `.env` que engana, porque cada
    ferramenta interpreta um pouco diferente.
    """
    valores: dict[str, str] = {}
    for linha in texto.splitlines():
        crua = linha.strip()
        if not crua or crua.startswith("#") or "=" not in crua:
            continue
        chave, _, valor = crua.partition("=")
        chave = chave.strip()
        if not chave or not chave.replace("_", "").isalnum():
            continue
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        valores[chave] = valor
    return valores


def carregar(diretorio: str | os.PathLike[str] | None = None) -> list[str]:
    """Aplica o `.env` do diretório ao ambiente do processo.

    Devolve as CHAVES aplicadas (nunca os valores — este arquivo costuma ter
    senha e token dentro). Variável que já existe no ambiente não é tocada.
    """
    caminho = Path(diretorio or Path.cwd()) / NOME
    if not caminho.is_file():
        return []
    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError:
        return []
    aplicadas = []
    for chave, valor in parse(texto).items():
        if chave in os.environ:
            continue  # o ambiente do processo ganha, sempre
        os.environ[chave] = valor
        aplicadas.append(chave)
    return aplicadas
