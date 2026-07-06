# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Context

A "Tendência diária" era calculada com `COUNT(*)` sobre `result_events`
(o log de transições gravado a cada mudança de status). Como cada arrasto
no kanban grava um evento, um único CT movido por vários status no mesmo
dia era contado como vários resultados — inflando o gráfico ("parece 9
resultados, mas é 1 CT"). A correção conta o **resultado líquido**: cada
par (execução, CT) conta uma vez por dia, pelo status da última transição
daquele dia.

## Requirements (EARS) — deltas

### Ubiquitous (MODIFIED)

- The system shall calcular a tendência diária contando cada par
  (execução, testcase) **uma vez por dia**, pelo status da última
  transição registrada naquele dia — nunca somando transições
  intermediárias.

### Unwanted-behavior (must-not) (ADDED)

- The system shall not inflar a tendência contabilizando transições
  intermediárias de status: reordenar/re-arrastar um mesmo CT entre
  colunas no mesmo dia não pode aumentar a contagem daquele dia.

## Acceptance criteria (ADDED)

5. [unverified] Um único CT arrastado por vários status no mesmo dia
   conta como 1 no status final do dia na tendência, não como vários —
   verified by `backend/tests/test_metrics.py`.
