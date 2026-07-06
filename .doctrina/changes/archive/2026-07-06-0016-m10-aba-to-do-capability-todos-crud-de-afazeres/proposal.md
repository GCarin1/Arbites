# Change 0016-m10-aba-to-do-capability-todos-crud-de-afazeres — M10 aba To-Do: capability todos — CRUD de afazeres em todos/*.md com status (open/doing/blocked/done), due, squad e links para CT/execucao/story; indice e filtros; frontend lista com filtros e historico

- **Status:** proposed
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** todos

## Why

M10 aba To-Do: capability todos — CRUD de afazeres em todos/*.md com status (open/doing/blocked/done), due, squad e links para CT/execucao/story; indice e filtros; frontend lista com filtros e historico

## What

- **workspace.py** — prefixo `todo` (`TD-`) e subdir `todos/`.
- **indexer.py** — tabela `todos` (status/due/squad/links/created); `_insert_todo`;
  loops de reindex completo e incremental; `_find_id` inclui todos.
- **api.py** — models `TodoIn/TodoUpdate`; CRUD `GET/POST/PUT/DELETE /todos`;
  filtros (status, squad, due_from/due_to, link); resolução dos títulos dos
  artefatos linkados (`_resolve_link`).
- **Frontend** — nova aba **Afazeres** (`Todos.tsx`): lista de ativos + histórico
  de concluídos, troca rápida de status, prazo com destaque de atraso, chips de
  link, e modal de criação/edição (título/status/prazo/squad/links).
- **Testes** — `backend/tests/test_todos.py` (CRUD, filtros, histórico, links).

## Scope boundaries

- Sem digestão por IA / daily (é M11, capability `daily`).
- Link é ponteiro por ID; título resolvido para exibição, link pendente não quebra.
- UI é lista com filtros; kanban arrastável fica no Future da spec.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 81 + build do frontend).
- [x] Os 4 critérios de `todos` verificados por `backend/tests/test_todos.py` (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
