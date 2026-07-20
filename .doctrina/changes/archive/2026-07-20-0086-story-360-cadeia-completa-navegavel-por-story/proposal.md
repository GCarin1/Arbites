# Change 0086-story-360-cadeia-completa-navegavel-por-story — story 360: cadeia completa navegavel por story

- **Status:** applied
- **Applied:** 2026-07-20
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** requirements

## Why

A cadeia Epic → Story → CT → Execution → Evidência → Defeito é a tese
do produto, mas está espalhada em 4+ telas e na matriz. Não existe UMA visão
que responda "essa história foi validada? qual evidência comprova?".

## What

- Backend: `GET /requirements/{id}/chain` — para uma story: meta + CTs
  (status doc, último resultado, nº de evidências) + executions que os
  rodaram + defeitos vinculados; SQL sobre tabelas existentes.
- Frontend: painel/tela "Story 360" aberto da aba Requisitos (botão na
  story): cadeia vertical navegável (cada nó clica para a tela do item),
  com dots de status e as evidências da última execução por CT.
- Segue o design system.

## Scope boundaries

- Somente leitura (nenhuma ação de edição dentro do 360).
- Não substitui a matriz de rastreabilidade (visão macro continua lá).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] `GET /requirements/{id}/chain` devolve a cadeia completa da story com último resultado e contagem de evidências por CT — `backend/tests/test_requirements.py` (ou novo test_chain).
- [x] Painel 360 navegável por nó — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
