# Change 0091-editor-e-lint-de-criterios-ears-na-story — editor e lint de criterios EARS na story

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** requirements

## Why

A spec de requirements diz "suporta critérios EARS no corpo" — mas é só
convenção de texto: sem templates, sem IDs estáveis, sem validação. É a
fundação do caminho "validador de SPEC" (0092/0093 dependem daqui).

## What

- Convenção parseável: seção `## Critérios de aceite` na story com itens
  `- [EARS-n] <frase EARS>`; parser extrai e indexa (tabela `criteria`:
  story_id, ord, texto, forma detectada).
- Editor de story: templates inseríveis dos 5 tipos EARS (ubiquitous/
  event/state/unwanted/optional) que geram o próximo `[EARS-n]`.
- Lint determinístico no reindex → warnings em Problemas: critério sem
  forma EARS reconhecível (sem shall/when/while), termos vagos
  configuráveis ("rápido", "alguns", "adequado"), critério duplicado.
- IA opcional "reescrever em EARS" (preview, provider existente).

## Scope boundaries

- Lint é warning, nunca bloqueia salvar.
- Vínculo critério↔CT fica na 0092; geração por critério na 0093.
- Stories legadas sem a seção não geram warning (opt-in pela presença da
  seção).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Parser extrai `[EARS-n]` e indexa; lint acusa frase sem forma EARS e termo vago; story sem seção não gera warning — `backend/tests/test_requirements.py` (ou test_ears.py).
- [ ] Templates no editor geram IDs sequenciais — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
