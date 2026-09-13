# Tasks — Change 0118-lista-ciclos-mostra-prazo

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `starts_on`/`ends_on` no tipo `ExecutionSummary` e exibidos na lista de ciclos, com a situação do prazo.
- [x] Vocabulário do ciclo (planejado / em andamento / fechado) também na lista, em vez do estado cru.
- [x] Extrair a leitura do prazo para um lugar só, usado pelo cabeçalho e pela lista.
- [x] Teste de que `GET /executions` devolve o período de cada ciclo.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0118-lista-ciclos-mostra-prazo/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
