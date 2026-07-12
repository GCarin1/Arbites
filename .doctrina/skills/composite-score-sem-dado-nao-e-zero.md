---
name: composite-score-sem-dado-nao-e-zero
description: Ao compor uma nota única (0-100) a partir de vários componentes com pesos, um componente sem dado suficiente deve virar `null` e ser excluído do cálculo (pesos restantes renormalizados) — nunca contar como 0.
when: O agente está implementando ou revisando uma métrica composta/ponderada (score único agregando várias sub-métricas) que pode rodar sobre um dataset vazio ou parcial.
---

# Skill — composite-score-sem-dado-nao-e-zero

## When to use this skill

- O agente está implementando um score composto (ex.: `health_score`) que
  combina N componentes com pesos configuráveis.
- O agente está revisando código onde `max(0, 100 - penalidade)` ou fórmula
  similar pode devolver um número "saudável" mesmo sem nenhum dado real
  (ex.: 0 defeitos porque não há nenhum registro, não porque está tudo bem).

## Procedure

1. Cada componente deve expor `value: number | null` — `null` quando não há
   dado suficiente para calcular (não confundir com "calculou e deu 0").
2. Ao agregar, componentes com `value is None` são excluídos do somatório e
   os pesos dos componentes restantes são renormalizados para somar 1.0 —
   nunca tratados como peso 0 aplicado a um valor 0.
3. Adicione um gate explícito de "há atividade real" (ex.:
   `EXISTS(SELECT 1 FROM testcases) OR EXISTS(SELECT 1 FROM defects)`) para
   cada componente que tem essa ambiguidade (contagem zero é indistinguível
   de ausência de dado). Sem esse gate, `max(0, 100 - 0)` mente dizendo 100.
4. Se TODOS os componentes ficarem `null`, o score geral também deve ser
   `null` — nunca 0 nem 100. Escreva um teste explícito de workspace vazio.
5. Sempre devolva a fórmula e o peso de cada componente na resposta (nada
   escondido atrás do número final).

## Anti-patterns

- Calcular `100 - penalidade` sem checar se há dado — um workspace vazio
  aparenta "100% saudável" (falso positivo).
- Tratar ausência de dado como pior caso (0) — um componente novo sem dados
  ainda derruba a nota geral injustamente (falso negativo).
- Peso fixo não renormalizado quando um componente é excluído — a soma dos
  pesos aplicados fica < 1.0 e o score fica artificialmente baixo.

## Related material

- `backend/arbites/metrics.py` — `health_score()`.
- `.doctrina/specs/reporting/spec.md` — critério de aceitação #12.
- [[template-fallback-precisa-de-none-nao-string-vazia]] — mesma família de
  bug (`None` vs valor "vazio" tratados como equivalentes quando não são).
