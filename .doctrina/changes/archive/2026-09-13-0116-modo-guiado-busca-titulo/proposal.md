# Change 0116-modo-guiado-busca-titulo — modo guiado busca o titulo de cada caso numa requisicao por caso em vez de uma so, como o Kanban faz

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

modo guiado busca o titulo de cada caso numa requisicao por caso em vez de uma so, como o Kanban faz

## What

- `executions` (spec MODIFIED): a regra de resolução de títulos passa a ser
  a mesma nas duas telas.
- `frontend/src/components/ExecutionGuided.tsx`: uma leitura de
  `GET /testcases` no lugar de uma requisição por caso.
- `backend/tests/test_executions_guided.py`: a prova de que a lista entrega
  o título de todos os casos do ciclo numa leitura só.

## Scope boundaries

- Não muda nenhum endpoint: `GET /testcases` já devolve o que o modo guiado
  precisa.
- Não mexe no Kanban, que já estava certo — é ele que define o padrão aqui.
- Não introduz cache entre telas; o ganho vem de pedir uma vez, não de
  guardar.

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
