# Change 0087-cobertura-semantica-passando-falhando-ou-nunca — cobertura semantica: passando, falhando ou nunca executada

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** requirements

## Why

A 0068 mostra "coberta (N CTs)" — mas coberta E PASSANDO? Story com CT
falhando aparece igual a story verde. O reporte fica menos honesto do que os
dados permitem.

## What

- `metrics.traceability` enriquecida com o último resultado por CT (da
  tabela `results`), agregando por story: `passing` (todos os CTs com
  último resultado passed), `failing` (algum failed/blocked), `untested`
  (nenhum CT executado).
- Aba Requisitos: badge de 4 estados — sem cobertura / coberta-nunca-
  executada / coberta-com-falhas / coberta-e-passando; filtro por estado.
- Dashboard/matriz reusa o mesmo dado (fonte única).

## Scope boundaries

- "Último resultado" = status mais recente por CT (qualquer execution);
  sem janela de sprint na v1.
- Não muda o cálculo de cobertura estrutural existente (só adiciona a
  camada semântica).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Story com CT failed → `failing`; todos passed → `passing`; CTs nunca executados → `untested` — `backend/tests/test_metrics.py`.
- [ ] Badges de 4 estados + filtro na aba Requisitos — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
