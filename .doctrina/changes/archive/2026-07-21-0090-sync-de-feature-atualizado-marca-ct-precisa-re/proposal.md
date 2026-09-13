# Change 0090-sync-de-feature-atualizado-marca-ct-precisa-re — sync de feature atualizado marca CT precisa re-execucao

- **Status:** applied
- **Applied:** 2026-07-21
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** local-automation, testcases

## Why

O feature-sync (0075) detecta steps `modified` e re-baseia o corpo do
CT no apply — mas o sinal morre aí: nada indica que aquele CT precisa ser
re-executado após a mudança.

## What

- Ao aplicar "update" (re-base de steps) no features-sync/apply, o CT
  ganha `needs_rerun: true` no frontmatter (indexado).
- O flag é limpo automaticamente quando um resultado novo do CT é
  registrado em qualquer execution posterior.
- Badge "precisa re-execução" no repositório de CTs e no board; filtro por
  flag no `GET /testcases`.

## Scope boundaries

- Só marca no APPLY consciente (cenário modificado sem apply já aparece
  no modal de sync — não duplicar o sinal).
- Não dispara execução automática.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Apply de update marca needs_rerun; resultado novo limpa; filtro funciona — `backend/tests/test_feature_sync.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
