# Change 0088-diff-entre-duas-executions — diff entre duas executions

- **Status:** applied
- **Applied:** 2026-07-21
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** executions

## Why

Comparar duas rodadas da mesma suíte (o que regrediu, o que foi
consertado) hoje é olho a olho entre dois boards. SQL trivial sobre
`results` resolve.

## What

- Backend: `GET /executions/diff?a=&b=` → categorias por CT presente em
  a e/ou b: `regressed` (passed→failed/blocked), `fixed` (failed→passed),
  `added`, `removed`, `unchanged` (com os dois status).
- UI: na tela Executions, modo "Comparar" (selecionar 2) → painel com as
  categorias em seções, cada CT navegável.

## Scope boundaries

- Compara resultados finais (não steps nem evidências).
- Sem diff de 3+ executions.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Diff classifica regressed/fixed/added/removed/unchanged corretamente — `backend/tests/test_executions.py`.
- [x] UI de comparação navegável — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
