# Change 0127-quadro-execucao-so-funciona — quadro de execucao so funciona com mouse: arrastar um card e impossivel pelo teclado

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

quadro de execucao so funciona com mouse: arrastar um card e impossivel pelo teclado

## What

- `design-system` (spec MODIFIED): o quadro passa a ser operável sem mouse
  e a se identificar para tecnologia assistiva.
- `frontend/src/components/Executions.tsx`: foco, teclado, rótulos e a
  região viva.
- `frontend/src/styles.css`: a dica do atalho e o realce de foco no card.

## Scope boundaries

- Não remove o arrastar: ele continua sendo o gesto rápido de quem usa
  mouse. O que muda é deixar de ser o único.
- Não implementa navegação bidimensional por setas entre os cards; o Tab já
  alcança todos, e o que faltava era mover, não circular.
- Não mexe no Modal, que já tem papel de diálogo, Esc e devolução de foco.
- Não toca nas regras de resultado: mover pelo teclado chama exatamente o
  mesmo caminho que arrastar.

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
