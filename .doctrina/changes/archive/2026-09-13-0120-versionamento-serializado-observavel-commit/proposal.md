# Change 0120-versionamento-serializado-observavel-commit — versionamento serializado e observavel: commit fora do event loop e falha registrada em vez de perdida

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** testcases

## Why

versionamento serializado e observavel: commit fora do event loop e falha registrada em vez de perdida

## What

- `testcases` (spec MODIFIED): o versionamento passa a ser serializado,
  fora do event loop e observável quando falha.
- `backend/arbites/versioning.py`: a fila por processo e o log de aviso.
- `backend/arbites/api.py`: as chamadas de commit fora do laço de eventos.
- `backend/tests/test_versioning.py`: concorrência e falha observável.

## Scope boundaries

- Não muda a regra da 0112 de que o git nunca derruba a escrita do usuário;
  muda o que acontece com o registro que não foi feito.
- Não coordena processos diferentes: a fila é do processo, que é como a
  aplicação roda hoje (um uvicorn, um processo). Rodar com dois ou mais
  workers passa a exigir decisão própria.
- Não muda o que é versionado nem a forma dos commits.

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
