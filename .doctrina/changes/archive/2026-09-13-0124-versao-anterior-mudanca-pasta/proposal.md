# Change 0124-versao-anterior-mudanca-pasta — versao anterior a mudanca de pasta e listada no historico mas nao abre nem restaura

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain; signals: mudanca)
- **Affects specs:** testcases

## Why

versao anterior a mudanca de pasta e listada no historico mas nao abre nem restaura

## What

- `testcases` (spec MODIFIED): as operações de versão passam a resolver o
  caminho de cada commit.
- `backend/arbites/versioning.py`: `history()` carrega o caminho por versão
  e um `path_at()` que o resolve para ver, comparar e restaurar.
- `backend/tests/test_versioning.py`: as três operações atravessando uma
  mudança de pasta.

## Scope boundaries

- Restaurar continua devolvendo o CONTEÚDO de uma versão anterior para o
  caminho atual do caso; não move o arquivo de volta para a pasta antiga.
  Restaurar texto e desfazer uma organização são duas ações diferentes.
- Não muda o `--follow` nem o formato do histórico exposto.

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
