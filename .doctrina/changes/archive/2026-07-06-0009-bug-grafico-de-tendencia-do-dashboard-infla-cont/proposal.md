# Change 0009-bug-grafico-de-tendencia-do-dashboard-infla-cont — bug: grafico de Tendencia do Dashboard infla contagem porque conta cada transicao de status (result_events) em vez do resultado liquido por CT/execucao/dia; um unico CT arrastado por varios status aparece como varios resultados

- **Status:** proposed
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** reporting

## Why

bug: grafico de Tendencia do Dashboard infla contagem porque conta cada transicao de status (result_events) em vez do resultado liquido por CT/execucao/dia; um unico CT arrastado por varios status aparece como varios resultados

## What

- `backend/arbites/metrics.py` — `trend()` passa a contar o **resultado
  líquido** do dia: cada par (execução, testcase) conta uma vez, pelo status
  da última transição daquele dia (window `ROW_NUMBER() … PARTITION BY
  execution_id, testcase_id, dia ORDER BY at DESC`), filtrando para
  passed/failed/blocked só depois de escolher a última. Antes era `COUNT(*)`
  sobre todas as transições em `result_events`.
- `backend/tests/test_metrics.py` — novo teste
  `test_trend_does_not_inflate_from_repeated_moves` (SC5) + o
  `test_trend_counts_daily_events` existente continua válido.
- Delta de spec `reporting`: critério de tendência por resultado líquido +
  unwanted-behavior contra inflar por transições intermediárias.

### Diagnóstico (por que só a tendência)

O `execution.json` guarda **1 resultado por CT** (atualizado no lugar) e a
tabela SQLite `results` tem PK `(execution_id, testcase_id)`. Logo o **kanban
de Execuções**, a **lista** (`result_counts`) e os **cards de KPI**
(pass_rate, coberturas, blocked_rate — todos sobre estado atual) já contam
1 CT como 1. Só a `trend()` lia o log de transições `result_events` cru. O
`rework_rate` e o `flaky` também usam o log mas já deduplicam por
execução/CT, então não infla. Verificado por reprodução automatizada contra
o backend e inspeção do workspace real (`EXEC-0001`: 1 resultado, 14 eventos).

## Scope boundaries

- **Não** altera o kanban de Execuções nem `set_result_status` — o
  armazenamento está correto (1 resultado por CT). Não foi possível
  reproduzir a duplicação "1 em blocked + 1 em failed" no kanban; os dados
  em disco têm resultado único. Se o usuário observar isso literalmente no
  kanban (e não no gráfico), reabrir com passos de reprodução.
- **Não** mexe em `rework_rate`/`flaky` (já deduplicados).
- **Não** grava/limpa o histórico `result_events` (continua sendo log fiel
  de transições); apenas muda como a tendência o agrega.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (typecheck/test/build — inclui `pytest` e build do frontend).
- [x] Novo critério SC5 de `reporting` coberto por `backend/tests/test_metrics.py::test_trend_does_not_inflate_from_repeated_moves` (`doctrina coverage`).
- [x] Reprodução do bug: 1 CT arrastado por 5 status no mesmo dia → tendência conta `(passed=0, failed=0, blocked=1)`, não 5.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
