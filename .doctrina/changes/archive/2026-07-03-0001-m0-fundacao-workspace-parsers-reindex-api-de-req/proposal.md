# Change 0001-m0-fundacao-workspace-parsers-reindex-api-de-req — M0 - fundacao: workspace, parsers, reindex, API de requisitos/testcases, UI basica, README com passo a passo para executar o projeto

- **Status:** proposed
- **Date:** 2026-07-03
- **Owner:** Gcarini
- **Affects specs:** workspace-core, indexing, requirements, testcases

## Why

M0 é o walking skeleton do produto (product.md → Delivery order): sem
workspace, parsers, reindex e a API/UI básicas, nenhuma outra capability
tem onde existir. Critério de pronto do milestone = SC1: criar epic, story
e CT pela UI; editar o mesmo CT em editor externo e ver a mudança refletida
sem ação manual; apagar `index.db`, reindexar e nada se perder.

## What

- `backend/` — pacote Python `arbites`: config (`arbites.yaml`), workspace
  service (estrutura, trash, contadores), parser (frontmatter + headings),
  indexer SQLite (reindex completo + incremental), warnings de
  integridade, watcher (watchdog), API FastAPI do M0
  (`/workspace`, `/workspace/reindex`, `/warnings`, `/tree`,
  `/requirements[...]`, `/testcases[...]` + `/raw`), servindo o build da
  SPA como estático.
- `backend/tests/` — pytest cobrindo os critérios de aceite de
  workspace-core, indexing (exceto Gherkin, que é M3), requirements e
  testcases.
- `frontend/` — React 18 + Vite + TS: árvore de testcases, editor de CT
  (form + aba markdown cru), lista/editor de requisitos, tela Problemas.
- `README.md` — passo a passo para instalar e executar (backend, frontend,
  dev mode e produção local).
- Deltas: avançar `Implementation` das 4 specs afetadas e apontar os
  critérios de aceite para os testes reais em `backend/tests/`.

## Scope boundaries

- Sem scan de Gherkin/features (indexing fica `partial`; scan é M3).
- Sem executions, defeitos, métricas, import Xray, runs, IA (M1+).
- UI sem Kanban e sem dashboard (M1/M1.5); apenas as telas do M0.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
