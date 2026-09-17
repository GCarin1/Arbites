"""Até onde já se olhou — e por que isso NÃO é derivável do disco.

## O problema

A marca d'água da ingestão é o disco (ADR 0016): "o que já ingeri" é a
pergunta que o próprio conteúdo responde, e por isso ingerir duas vezes não
duplica nada. Isso continua valendo e não muda aqui.

Só que existe uma segunda pergunta, e essa o disco não responde: **até onde
eu já olhei?** Um mês sem nenhuma execução e um mês nunca varrido são
exatamente a mesma coisa no disco — nenhum arquivo. Sem registrar a
cobertura, toda busca recomeça do zero, e trocar o período de 30 para 90
dias re-lista os 30 que já estavam lá.

## Por que um arquivo, e o que acontece se ele sumir

Fica em `ci/cobertura.json`, no workspace, aberto e legível como todo o
resto. Perdê-lo custa TEMPO, nunca dados: sem ele a próxima busca varre a
janela inteira de novo e o disco continua impedindo a duplicação. É uma
otimização com registro honesto, não uma fonte de verdade paralela.

## Por que uma LISTA de intervalos

Um intervalo só seria mais simples e mentiria. A busca é limitada por
`max_runs_per_poll`: pedir 90 dias pode cobrir só os 20 mais recentes da
lacuna. Guardar isso como um intervalo contíguo com o que já havia afirmaria
ter olhado um pedaço que ninguém olhou — e esse pedaço nunca mais seria
varrido, que é o pior defeito possível numa série temporal.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

NOME = "cobertura.json"
VERSAO = 1


def chave_da_fonte(fonte: dict[str, Any]) -> str:
    """Cobertura é POR FONTE: cada repositório é varrido por conta própria,
    e o workflow faz parte da identidade — filtrar por um workflow não diz
    nada sobre os outros."""
    return (f"{fonte.get('provider', 'github')}:{fonte.get('repo')}"
            f":{fonte.get('workflow') or '*'}")


def caminho(ws) -> Path:
    return ws.root / "ci" / NOME


def ler(ws) -> dict[str, list[list[str]]]:
    """Os intervalos cobertos por fonte. Arquivo ausente ou corrompido
    responde "nada coberto": degradar para trabalho a mais é sempre melhor
    que degradar para trabalho a menos."""
    alvo = caminho(ws)
    if not alvo.is_file():
        return {}
    try:
        dados = json.loads(alvo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(dados, dict) or dados.get("version") != VERSAO:
        return {}
    fontes = dados.get("sources")
    return fontes if isinstance(fontes, dict) else {}


def gravar(ws, fontes: dict[str, list[list[str]]]) -> None:
    alvo = caminho(ws)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(
        json.dumps({"version": VERSAO, "sources": fontes},
                   indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def fundir(intervalos: list[list[str]]) -> list[list[str]]:
    """Une os intervalos que se tocam; mantém separados os que não se tocam.

    Manter separado é o ponto: dois intervalos com um buraco entre eles
    descrevem exatamente o que aconteceu quando a busca parou no limite.
    """
    limpos = sorted([list(i) for i in intervalos if len(i) == 2 and i[0] <= i[1]])
    if not limpos:
        return []
    saida = [limpos[0]]
    for inicio, fim in limpos[1:]:
        if inicio <= saida[-1][1]:
            saida[-1][1] = max(saida[-1][1], fim)
        else:
            saida.append([inicio, fim])
    return saida


def lacunas(intervalos: list[list[str]], desde: str,
            ate: str) -> list[tuple[str, str]]:
    """O que falta varrer em [desde, ate] — a conta que evita o retrabalho."""
    if desde >= ate:
        return []
    faltando: list[tuple[str, str]] = []
    cursor = desde
    for inicio, fim in fundir(intervalos):
        if fim <= cursor:
            continue
        if inicio >= ate:
            break
        if inicio > cursor:
            faltando.append((cursor, min(inicio, ate)))
        cursor = max(cursor, fim)
        if cursor >= ate:
            return faltando
    if cursor < ate:
        faltando.append((cursor, ate))
    return faltando


def registrar(ws, fonte: dict[str, Any], desde: str, ate: str) -> None:
    """Marca [desde, ate] como varrido para esta fonte."""
    if desde >= ate:
        return
    fontes = ler(ws)
    chave = chave_da_fonte(fonte)
    fontes[chave] = fundir(list(fontes.get(chave) or []) + [[desde, ate]])
    gravar(ws, fontes)


def cobertura_da_fonte(ws, fonte: dict[str, Any]) -> list[list[str]]:
    return list(ler(ws).get(chave_da_fonte(fonte)) or [])


def esquecer(ws, fonte: dict[str, Any] | None = None) -> None:
    """Apaga a cobertura — de uma fonte, ou de todas.

    Existe porque "varra tudo de novo" precisa ser possível sem apagar dado:
    quem desconfia do que está na tela tem de poder mandar reconferir.
    """
    if fonte is None:
        alvo = caminho(ws)
        alvo.unlink(missing_ok=True)
        return
    fontes = ler(ws)
    fontes.pop(chave_da_fonte(fonte), None)
    gravar(ws, fontes)
