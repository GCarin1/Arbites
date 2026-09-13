# Change 0118-lista-ciclos-mostra-prazo — lista de ciclos nao mostra prazo nem o vocabulario do ciclo, entao saber qual esta atrasado exige abrir um por um

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

lista de ciclos nao mostra prazo nem o vocabulario do ciclo, entao saber qual esta atrasado exige abrir um por um

## What

- `executions` (spec MODIFIED): prazo e vocabulário do ciclo também na
  lista.
- `frontend/src/components/Executions.tsx`: a situação do prazo e o estado
  legível em cada linha; `deadlineNote` e `CYCLE_LABELS` passam a servir as
  duas telas.
- `frontend/src/types.ts`: `starts_on`/`ends_on` no `ExecutionSummary`.
- `backend/tests/test_execution_cycle.py`: a prova de que a lista devolve o
  período.

## Scope boundaries

- Não muda endpoint nem índice: `GET /executions` já devolve as duas datas
  desde a change 0111.
- Não cria filtro por prazo nem ordenação por atraso; a mudança é mostrar o
  que já existe, e filtrar é outra conversa.
- Não renomeia `draft` no disco — a ADR 0013 decidiu isso e continua
  valendo.

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

Nenhuma.
