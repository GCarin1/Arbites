# Tasks — Change 0111-execution-como-ciclo-de-teste

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `starts_on`/`ends_on` no `execution.json` e no `PATCH /executions/{id}`, com recusa de período invertido (422).
- [x] `assignee` por resultado + `POST /executions/{id}/results/{ct}/assignee`, com evento no `history[]`.
- [x] Índice: colunas `starts_on`/`ends_on` em `executions` e `assignee` em `results`, com migração tolerante.
- [x] `backend/tests/test_execution_cycle.py` provando período, responsável, contadores e leitura de `execution.json` antigo.
- [x] Cabeçalho de progresso no padrão Xray: barra empilhada, contadores grandes por status, total e situação do prazo.
- [x] Vocabulário planejado / em andamento / fechado na interface e responsável visível no card do Kanban.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0111-execution-como-ciclo-de-teste/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
