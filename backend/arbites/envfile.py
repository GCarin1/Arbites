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

# Quantos níveis subir procurando o arquivo. O `README` manda `cd backend`
# antes do `serve`, e o `.env` de quase todo mundo está na RAIZ do projeto —
# um nível acima. Sem subir, o arquivo existe, está certo, e nunca é lido.
# O limite existe para não sequestrar um `.env` da pasta pessoal de alguém:
# cinco níveis cobrem qualquer projeto e param bem antes disso.
NIVEIS = 5


def pista_do_valor(valor: str) -> str | None:
    """O que há de suspeito no valor, dito por extenso.

    `repr()` mostra tudo, mas só para quem sabe ler `repr()`. Estas três
    formas são as que a pessoa digita achando que está certo.
    """
    if "\\\\" in valor:
        return ("o valor tem barras invertidas DUPLICADAS. O `.env` não"
                " interpreta escapes: o que chega ao Python são duas barras"
                " mesmo. Use uma só, ou barras normais (`C:/Users/...`), que"
                " o Python aceita no Windows.")
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        return ("o valor ainda tem aspas depois da leitura — provavelmente"
                " aspas duplas dentro de simples, ou o contrário.")
    if valor != valor.strip():
        return "o valor tem espaço no começo ou no fim."
    if valor.startswith("~") or ("%" in valor and valor.count("%") >= 2):
        return ("o valor tem `~` ou `%VARIAVEL%`: o `.env` não expande"
                " nenhum dos dois. Escreva o caminho completo.")
    return None


def parse(texto: str) -> dict[str, str]:
    """Formato mínimo e previsível: `CHAVE=valor`, `#` comenta, aspas saem.

    Não interpreta `export`, substituição de variável nem várias linhas: um
    `.env` que se comporta como shell é um `.env` que engana, porque cada
    ferramenta interpreta um pouco diferente.
    """
    valores: dict[str, str] = {}
    for linha in texto.lstrip("\ufeff").splitlines():
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


def localizar(diretorio: str | os.PathLike[str] | None = None) -> Path | None:
    """O `.env` do diretório, ou o primeiro subindo até `NIVEIS` pais.

    Procurar só no diretório atual parecia a regra mais previsível, e era a
    mais cruel: o comando documentado é `cd backend && python -m arbites
    serve`, o `.env` de todo mundo está na raiz do projeto, e o resultado era
    um arquivo perfeito que o processo nunca leu — sem nenhum sinal disso
    (change 0187). Quem sobe agora imprime QUAL arquivo usou, que é o que
    torna a busca honesta.
    """
    base = Path(diretorio or Path.cwd()).resolve()
    for pasta in [base, *base.parents][:NIVEIS + 1]:
        candidato = pasta / NOME
        if candidato.is_file():
            return candidato
    return None


def carregar(diretorio: str | os.PathLike[str] | None = None) -> list[str]:
    """Aplica o `.env` encontrado ao ambiente do processo.

    Devolve as CHAVES aplicadas (nunca os valores — este arquivo costuma ter
    senha e token dentro). Variável que já existe no ambiente não é tocada.
    """
    caminho = localizar(diretorio)
    if caminho is None:
        return []
    try:
        # `utf-8-sig` e não `utf-8`: o Bloco de Notas do Windows grava BOM,
        # e com ele a PRIMEIRA chave do arquivo vira `\ufeffARBITES_...`, que
        # não passa no teste de nome e era descartada EM SILÊNCIO. Um `.env`
        # perfeito em que só a primeira linha não vale é indepurável por
        # leitura (change 0187).
        texto = caminho.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    aplicadas = []
    for chave, valor in parse(texto).items():
        if chave in os.environ:
            continue  # o ambiente do processo ganha, sempre
        os.environ[chave] = valor
        aplicadas.append(chave)
    return aplicadas


def descartadas(texto: str) -> list[tuple[int, str, str]]:
    """As linhas que PARECEM atribuição e não viraram variável.

    O parser ignora o que não entende, e ignorar em silêncio é o pior modo de
    falhar num arquivo de configuração: o arquivo parece certo, a variável não
    chega, e não há nada a depurar. Isto existe para o diagnóstico poder
    apontar a linha e o motivo (change 0187).

    Devolve `(numero_da_linha, motivo, trecho_sem_valor)` — o valor nunca
    entra no trecho: este arquivo tem senha e token dentro.
    """
    saida: list[tuple[int, str, str]] = []
    for numero, linha in enumerate(texto.lstrip("\ufeff").splitlines(), start=1):
        crua = linha.strip()
        if not crua or crua.startswith("#"):
            continue
        if "=" not in crua:
            saida.append((numero, "nao tem `=`", crua[:40]))
            continue
        chave = crua.partition("=")[0].strip()
        if not chave:
            saida.append((numero, "nome vazio antes do `=`", "= ..."))
            continue
        if chave.startswith("export "):
            saida.append((numero, "comeca com `export`, que este leitor nao"
                          " interpreta — apague a palavra", f"{chave} = ..."))
            continue
        if not chave.replace("_", "").isalnum():
            motivo = ("caractere invisivel no nome (BOM?)"
                      if not chave.isprintable()
                      else "o nome tem caractere que nao e letra, numero ou `_`")
            saida.append((numero, motivo, f"{chave!r} = ..."))
    return saida
