# Change 0093-gerar-cts-por-criterio-ears-com-vinculo-gravado — gerar CTs por criterio EARS com vinculo gravado

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** ai-assist, testcases

## Why

A IA gera CTs da story inteira — o vínculo fino critério→CT (que a 0092
audita) teria de ser preenchido à mão. Gerar POR critério grava o vínculo de
graça e fecha o loop do validador de SPEC.

## What

- Aba IA · Gerar: ao informar story com critérios EARS (0091), listar os
  critérios com checkbox; "gerar por critério" produz CTs por critério
  selecionado (prompt focado no critério + contexto da story).
- CT aceito grava `story` + `criteria: [EARS-n]` automaticamente.
- Fallback: story sem critérios mantém o fluxo atual (geração da story
  inteira, sem vínculo fino).

## Scope boundaries

- Depende de 0091 (parse) e 0092 (campo `criteria`).
- Preview obrigatório inalterado (nada gravado sem aceite).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Geração por critério envia o critério no prompt e o aceite grava `criteria` — `backend/tests/test_ai_generate.py` (MockTransport).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
