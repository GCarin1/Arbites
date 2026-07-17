# Change 0069-deletar-test-execution-pela-ui-delete-executions — Deletar test execution pela UI: DELETE /executions/{id} move a pasta para a lixeira e reindexa; botao Excluir com ConfirmModal no repositorio de execucoes; execution com run ativo nao pode ser deletada

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** executions

## Why

Deletar test execution pela UI: DELETE /executions/{id} move a pasta para a lixeira e reindexa; botao Excluir com ConfirmModal no repositorio de execucoes; execution com run ativo nao pode ser deletada

## What

Novo `DELETE /executions/{id}`: move a PASTA da execution
(`executions/<ano>/<id>/`, incluindo evidências) para a lixeira
(`.arbites/trash/`) e reindexa — padrão de trash igual aos demais
artefatos. UI: botão Excluir com ConfirmModal no repositório de execuções.
Execution com run ativo (runner) retorna 409.

## Scope boundaries

Hard delete nunca (lixeira sempre). Não deleta em massa (uma por vez).
Resultados/result_events da execution saem do índice junto (reindex).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
