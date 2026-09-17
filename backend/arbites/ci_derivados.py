"""Medidas que o Arbites calcula sobre a execução (ADR 0019, change 0194).

## O problema que isto resolve

45 execuções ingeridas, 1367 violações de acessibilidade lidas, 405 cenários
extraídos — e "Sinais no tempo" vazio. Toda a matéria-prima estava no disco,
e o único eixo que faz um dashboard virar observabilidade ("está piorando?")
não existia, porque a tela esperava um `arbites.json` que o pipeline de outro
time não tem como publicar hoje.

## A fronteira, que é o ponto inteiro

A ADR 0016 proíbe **inferir semântica**: ler `42` de um `metrics.json`
qualquer e chamar de "latência" produz um gráfico que parece informação e não
é. Isso continua proibido, e nada aqui o afrouxa.

O que este módulo faz é outra coisa: aritmética sobre fatos que o Arbites
**já apurou**. Ele sabe quanto durou a execução porque tem os horários do
provedor; sabe quantos cenários falharam porque leu o relatório Cucumber, cujo
formato é documentado; sabe quantos elementos violam WCAG porque leu o
axe-core, idem. Nomear e datar esses números não é adivinhar.

Reconhecer um formato documentado é leitura. Adivinhar o significado de um
número solto é invenção. A fronteira é essa.

## As três regras

1. **O declarado vence pelo NOME.** Manifesto que declara `duracao_s` desliga
   o derivado homônimo. Quem produz sabe mais.
2. **Sem fonte, sem sinal.** Não há relatório Cucumber? Não há sinal de
   cenário. Zero inventado é pior que ausência: zero é um ponto no gráfico,
   ausência não é.
3. **O conjunto é FECHADO.** Está aqui, no código. Um conjunto aberto ao
   conteúdo do artifact voltaria a ser inferência com outro nome.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# `kind` separa o derivado do declarado já na tabela: quem consulta a série
# consegue filtrar sem depender do nome.
KIND = "derivado"
ORIGEM = "derivado"

# Gravidades do axe-core que ganham série própria. As duas que mandam num
# plano de correção — as outras entram no total e não viram linha.
GRAVIDADES = ("critical", "serious")


def derivar(meta: dict[str, Any], declarados: list[dict[str, Any]],
            quando: str) -> list[dict[str, Any]]:
    """As medidas do Arbites sobre esta execução, sem as que já foram declaradas."""
    ja_declarados = {str(s.get("name")) for s in declarados if s.get("name")}
    saida: list[dict[str, Any]] = []

    def por(nome: str, valor: float | None, unidade: str | None) -> None:
        if valor is None or nome in ja_declarados:
            return
        saida.append({"kind": KIND, "name": nome, "value": float(valor),
                      "unit": unidade, "at": quando, "source": ORIGEM})

    por("duracao_min", _duracao_min(meta), "min")
    # Sem unidade: "0/1" ao lado do número vira "0 0/1" no cartão, e o nome
    # da série já diz o que 1 e 0 significam.
    por("resultado", _resultado(meta), None)
    por("jobs_falhos", _jobs_falhos(meta), "count")

    cenarios = meta.get("scenarios") or []
    if cenarios:
        falhos = sum(1 for c in cenarios if _falhou(c.get("status")))
        por("cenarios", len(cenarios), "count")
        por("cenarios_falhos", falhos, "count")
        por("cenarios_taxa", round((len(cenarios) - falhos) / len(cenarios)
                                   * 100, 1), "%")

    achados = meta.get("findings") or []
    if achados:
        por("acessibilidade_violacoes",
            sum(_quantos(a) for a in achados), "count")
        for gravidade in GRAVIDADES:
            por(f"acessibilidade_{gravidade}",
                sum(_quantos(a) for a in achados
                    if (a.get("impact") or "").lower() == gravidade), "count")
        criterios = {a.get("wcag") for a in achados if a.get("wcag")}
        por("wcag_criterios_violados", len(criterios), "count")
    return saida


def _falhou(status: Any) -> bool:
    # "passed" é o único resultado que não é falha; `blocked`, `undefined` e
    # `pending` são cenários que não provaram nada, e tratá-los como verdes
    # infla a taxa exatamente onde ela precisa ser honesta.
    return str(status or "").lower() not in ("passed", "skipped")


def _quantos(achado: dict[str, Any]) -> int:
    try:
        return int(achado.get("count") or 0)
    except (TypeError, ValueError):
        return 0


def _duracao_min(meta: dict[str, Any]) -> float | None:
    """Minutos entre o início e o fim — em minutos, não segundos: uma suíte
    de regressão dura dezenas de minutos, e um eixo em milhares de segundos
    não se lê."""
    inicio, fim = _instante(meta.get("started_at")), _instante(meta.get("finished_at"))
    if inicio is None or fim is None or fim < inicio:
        return None
    return round((fim - inicio).total_seconds() / 60, 2)


def _resultado(meta: dict[str, Any]) -> float | None:
    """1 quando passou, 0 quando falhou — e NADA quando não houve veredito.

    A mesma regra da change 0191: cancelada e pulada não são zero. Zero seria
    um ponto no gráfico dizendo que quebrou, quando nada foi medido.
    """
    from .ci_ingest import SUCESSO, e_conclusiva

    conclusao = meta.get("conclusion")
    if not e_conclusiva(conclusao):
        return None
    return 1.0 if conclusao == SUCESSO else 0.0


def _jobs_falhos(meta: dict[str, Any]) -> float | None:
    jobs = meta.get("jobs") or []
    if not jobs:
        return None
    return float(sum(1 for j in jobs
                     if (j.get("conclusion") or "") not in ("success", "skipped")))


def _instante(bruto: Any) -> datetime | None:
    if not bruto:
        return None
    try:
        return datetime.fromisoformat(str(bruto).replace("Z", "+00:00"))
    except ValueError:
        return None
