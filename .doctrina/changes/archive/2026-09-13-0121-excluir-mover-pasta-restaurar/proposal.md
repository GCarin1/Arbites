# Change 0121-excluir-mover-pasta-restaurar — excluir mover pasta e restaurar da lixeira nao entram no versionamento e deixam o repositorio permanentemente sujo

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** chore (confident; signals: mover)
- **Affects specs:** testcases

## Why

excluir mover pasta e restaurar da lixeira nao entram no versionamento e deixam o repositorio permanentemente sujo

## What

- `testcases` (spec MODIFIED): as ações em lote entram no versionamento.
- `backend/arbites/api.py`: commit em excluir pasta, mover pasta e
  restaurar da lixeira.
- `backend/tests/test_versioning.py`: a prova de que o repositório não fica
  com pendência e de que o histórico sobrevive.

## Scope boundaries

- Não versiona os demais artefatos (requisito, defeito, execution): o
  escopo do versionamento continua sendo o caso de teste, como a change
  0112 decidiu.
- Não muda a lixeira: excluir continua movendo para `trash/`, e o commit
  apenas registra que saiu.
- Não reescreve histórico já gravado; o que ficou pendente de versões
  anteriores entra no próximo commit que tocar aqueles caminhos.

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
