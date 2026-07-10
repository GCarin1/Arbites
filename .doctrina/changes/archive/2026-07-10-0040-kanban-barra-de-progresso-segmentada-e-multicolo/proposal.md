# Change 0040-kanban-barra-de-progresso-segmentada-e-multicolo — kanban: barra de progresso segmentada e multicolor. No card, um segmento por passo colorido pelo status (verde passed, vermelho failed, laranja blocked), enchendo ate onde a execucao chegou. Na barra da execucao, empilhar todos os status por contagem com suas cores, nao so os passed

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** executions

## Why

kanban: barra de progresso segmentada e multicolor. No card, um segmento por passo colorido pelo status (verde passed, vermelho failed, laranja blocked), enchendo ate onde a execucao chegou. Na barra da execucao, empilhar todos os status por contagem com suas cores, nao so os passed

## What

- **frontend/src/components/Executions.tsx** — `StepBar` (barra segmentada por
  passo, cor por status) substitui o % único no card; `ExecStackBar` (barra
  empilhada por status) substitui o fill só-de-passed na execução.
- **frontend/src/styles.css** — `.stepbar/.seg-*` e `.exec-stack/.exec-seg.col-*`
  reusando as cores de status (`--success/--danger/--warning/--primary/--retest`).
- **executions spec** MODIFIED (barra segmentada + empilhada) + critério #5.

## Scope boundaries

- Só visual; nenhum campo novo no backend — tudo derivado de `steps[]`/colunas.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (121 testes backend + build).
- [x] Critério #5 do executions cita `backend/tests/test_executions.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
