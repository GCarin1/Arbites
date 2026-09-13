# Change 0132-acoes-empilhadas-linha-tabela — acoes empilhadas na linha da tabela inflam a altura e a acao destrutiva fica o elemento mais chamativo

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

acoes empilhadas na linha da tabela inflam a altura e a acao destrutiva fica o elemento mais chamativo

## What

- `design-system` (spec MODIFIED): ação de linha, identificador e caixa de
  marcar.
- `frontend/src/components/Defects.tsx`: as ações da linha no menu.
- `frontend/src/styles.css`: identificador sem quebra e o par
  caixa-rótulo.

## Scope boundaries

- Não remove nenhuma ação: editar continua na linha e excluir a dois
  cliques, com a mesma confirmação.
- Não mexe no seletor de status dentro da linha, que é edição rápida e não
  ação destrutiva.
- Não reescreve a tabela em cartão no celular, que continua rolando dentro
  do próprio bloco.

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
