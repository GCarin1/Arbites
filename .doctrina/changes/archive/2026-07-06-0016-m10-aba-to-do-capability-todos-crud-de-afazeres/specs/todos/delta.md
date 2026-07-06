# Spec Delta — capability: todos

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/todos/spec.md`

---

## Context

M10 entrega a capability: CRUD de afazeres em `todos/*.md`, tabela `todos`
no índice (status/due/squad/links), filtros por status/período/link,
resolução dos títulos dos artefatos linkados, e a aba **Afazeres** no
frontend (lista de ativos + histórico de concluídos, com modal de criação/
edição e troca rápida de status). Isto passa a Implementação de `planned`
→ `verified` e os quatro critérios de `[unverified]` → `[verified]`.

## Header (MODIFIED)

- **Implementation:** verified — M10 (backend/arbites/indexer.py,
  backend/arbites/api.py, backend/arbites/workspace.py; frontend
  Todos.tsx). ID `TD-`, arquivos em `todos/`.

## Acceptance criteria (MODIFIED — verificados)

1. [verified] CRUD de todo com status/due/squad/links persistido em
   `todos/*.md` e refletido no índice — verified by `backend/tests/test_todos.py`.
2. [verified] Filtrar todos por status e por período (`due`) retorna o
   subconjunto correto — verified by `backend/tests/test_todos.py`.
3. [verified] Todos `done` permanecem consultáveis por data (histórico não
   se perde) — verified by `backend/tests/test_todos.py`.
4. [verified] Links para CT/execução/story resolvem o título do artefato
   para exibição — verified by `backend/tests/test_todos.py`.
