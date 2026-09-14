"""Intercâmbio por arquivo: CSV e Cucumber JSON (change 0148, ADR 0015).

## Por que este adaptador existe, e por que ele vem ANTES dos de API

**1. É a resposta honesta a "independente da ferramenta".** Adaptador por API
só existe onde há API e permissão — e permissão, numa empresa, é pedido que
demora. Arquivo existe sempre: toda ferramenta de teste do mercado importa
CSV, e o Cucumber JSON já é lido aqui (`behave_json.py`). Sem credencial, sem
MCP, sem pedir nada para a TI.

**2. É o SEGUNDO adaptador — e é ele que valida a porta.** Não existe
abstração antes da segunda implementação: uma porta construída com UMA
ferramenta na mão sai com o formato daquela ferramenta. O adaptador de
arquivo é barato e força a porta a ser honesta antes que qualquer adaptador
de API dependa dela.

## O que ele NÃO faz, dito antes e não descoberto depois

- **Evidência sai como CAMINHO, nunca como binário embutido.** Um CSV com
  print em base64 fica intratável em qualquer planilha, e é o tipo de coisa
  que se descobre no meio de uma migração. A capacidade declarada já diz
  `evidence="path"`.
- **Não adivinha o dialeto de CSV de cada ferramenta.** O mapeamento de
  colunas é configuração; aqui o formato é neutro e explícito.
- **Coluna faltando não importa pela metade.** Importar 40 de 50 linhas e
  calar sobre as 10 é pior do que não importar: o buraco não aparece.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from . import integrations as integ_ops

# O formato NEUTRO. Não é o CSV de nenhuma ferramenta específica — é o que
# sobrevive à ida e à volta sem perder identidade, que é o requisito real.
COLUNAS_CASO = [
    "external_id",   # o id no sistema de origem: é ele que dá a idempotência
    "id",            # o id daqui (vazio na importação de algo novo)
    "title",
    "type",
    "priority",
    "status",
    "story",
    "tags",          # separadas por ";" — vírgula brigaria com o CSV
    "folder",
    "body",
]
COLUNAS_RESULTADO = [
    "execution_id",
    "testcase_id",
    "external_id",
    "status",
    "executed_at",
    "executed_by",
    "comment",
    "evidence_paths",  # CAMINHOS separados por ";", nunca o binário
]

SEPARADOR_LISTA = ";"


class ArquivoErro(Exception):
    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _linha_de_caso(meta: dict[str, Any], corpo: str, system: str) -> dict[str, str]:
    vinculo = integ_ops.link_for(meta, system) or {}
    return {
        "external_id": str(vinculo.get("id") or ""),
        "id": str(meta.get("id") or ""),
        "title": str(meta.get("title") or ""),
        "type": str(meta.get("type") or ""),
        "priority": str(meta.get("priority") or ""),
        "status": str(meta.get("status") or ""),
        "story": str(meta.get("story") or ""),
        "tags": SEPARADOR_LISTA.join(meta.get("tags") or []),
        "folder": str(meta.get("folder") or ""),
        "body": corpo or "",
    }


def exportar_casos(linhas: list[dict[str, Any]], system: str = "file") -> str:
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=COLUNAS_CASO, lineterminator="\n")
    escritor.writeheader()
    for item in linhas:
        escritor.writerow(_linha_de_caso(item["meta"], item["body"], system))
    return buffer.getvalue()


def exportar_resultados(execucoes: list[dict[str, Any]],
                        system: str = "file") -> str:
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=COLUNAS_RESULTADO,
                              lineterminator="\n")
    escritor.writeheader()
    for execucao in execucoes:
        for resultado in execucao.get("results") or []:
            escritor.writerow({
                "execution_id": execucao.get("id") or "",
                "testcase_id": resultado.get("testcase_id") or "",
                "external_id": resultado.get("external_id") or "",
                "status": resultado.get("status") or "",
                "executed_at": resultado.get("executed_at") or "",
                "executed_by": resultado.get("executed_by") or "",
                "comment": resultado.get("comment") or "",
                # caminho, não anexo: a capacidade declarada é `evidence=path`
                "evidence_paths": SEPARADOR_LISTA.join(
                    e.get("path", "") for e in resultado.get("evidences") or []
                ),
            })
    return buffer.getvalue()


def ler_csv(texto: str, obrigatorias: list[str]) -> list[dict[str, str]]:
    """Lê e VALIDA o cabeçalho antes de qualquer linha.

    Falhar na primeira linha ruim deixaria metade importada e metade não —
    e um import pela metade é pior do que nenhum, porque o buraco não aparece.
    """
    try:
        leitor = csv.DictReader(io.StringIO(texto))
        cabecalho = leitor.fieldnames or []
    except csv.Error as e:
        raise ArquivoErro("invalid_csv", f"CSV ilegível: {e}") from e
    if not cabecalho:
        raise ArquivoErro("empty_csv", "o arquivo não tem cabeçalho")

    faltando = [c for c in obrigatorias if c not in cabecalho]
    if faltando:
        raise ArquivoErro(
            "missing_column",
            "falta a coluna %s no CSV (colunas encontradas: %s)"
            % (", ".join(f"`{c}`" for c in faltando), ", ".join(cabecalho)),
        )
    return [dict(linha) for linha in leitor]


def previa_importacao(linhas: list[dict[str, str]], system: str,
                      achar) -> dict[str, Any]:
    """O plano: o que cria, o que atualiza e o que fica de fora.

    A idempotência vem do `external_id`, não da ordem das linhas: reimportar
    o mesmo arquivo encontra os mesmos vínculos e atualiza no lugar.
    """
    criar, atualizar, sem_identidade = [], [], []
    vistos: dict[str, int] = {}
    duplicados = []
    for numero, linha in enumerate(linhas, start=2):  # 1 é o cabeçalho
        titulo = (linha.get("title") or "").strip()
        externo = (linha.get("external_id") or "").strip()
        if not titulo:
            raise ArquivoErro(
                "missing_title", f"linha {numero}: `title` vazio")
        if not externo:
            # sem identidade externa não há como reconhecer na próxima vez:
            # importa, mas o preview DIZ que a volta não será idempotente
            sem_identidade.append({"line": numero, "title": titulo})
            criar.append({"line": numero, "title": titulo, "external_id": None})
            continue
        if externo in vistos:
            duplicados.append({"line": numero, "external_id": externo,
                               "first_line": vistos[externo]})
            continue
        vistos[externo] = numero
        existente = achar(system, externo)
        if existente:
            atualizar.append({"line": numero, "title": titulo,
                              "external_id": externo, "entity_id": existente})
        else:
            criar.append({"line": numero, "title": titulo, "external_id": externo})

    avisos = []
    capacidades = integ_ops.ADAPTADORES["file"]
    avisos.append(
        "evidência sai como CAMINHO relativo, não como anexo: o arquivo não"
        " carrega o binário do print, só onde ele está."
    )
    if sem_identidade:
        avisos.append(
            f"{len(sem_identidade)} linha(s) sem `external_id` — elas serão"
            " criadas, mas reimportar o mesmo arquivo criará de novo: sem"
            " identidade externa não há como reconhecer o que já entrou."
        )
    if duplicados:
        avisos.append(
            f"{len(duplicados)} linha(s) repetem um `external_id` que já"
            " apareceu antes no mesmo arquivo e foram ignoradas — duas linhas"
            " para o mesmo item tornam indecidível qual vale."
        )
    return {
        "system": system,
        "create": criar,
        "update": atualizar,
        "skipped_duplicates": duplicados,
        "without_identity": sem_identidade,
        "not_represented": capacidades.nao_representa(integ_ops.ARTEFATOS),
        "warnings": avisos,
    }


# -- Cucumber JSON -----------------------------------------------------------


def ler_cucumber(bruto: bytes | str) -> list[dict[str, Any]]:
    """Cenários de um Cucumber JSON, com a tag `@CT-XXXX` que os liga (ADR
    0003). Reaproveita o mesmo vocabulário do run local — o formato já é lido
    aqui, e ter dois parsers para o mesmo arquivo seria convidar a divergência.
    """
    try:
        dados = json.loads(bruto if isinstance(bruto, str) else bruto.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise ArquivoErro("invalid_json", f"Cucumber JSON ilegível: {e}") from e
    if not isinstance(dados, list):
        raise ArquivoErro(
            "invalid_cucumber",
            "Cucumber JSON é uma LISTA de features; recebido %s"
            % type(dados).__name__,
        )
    saida = []
    for feature in dados:
        for elemento in (feature or {}).get("elements") or []:
            tags = [t["name"] if isinstance(t, dict) else str(t)
                    for t in elemento.get("tags") or []]
            ct = next((t for t in tags if t.upper().startswith("@CT-")), None)
            passos = elemento.get("steps") or []
            falhou = any(
                (p.get("result") or {}).get("status") == "failed" for p in passos
            )
            saida.append({
                "feature": (feature or {}).get("name"),
                "scenario": elemento.get("name"),
                "testcase_id": ct[1:] if ct else None,
                "tags": tags,
                "status": elemento.get("status")
                or ("failed" if falhou else "passed"),
                "steps": len(passos),
            })
    return saida
