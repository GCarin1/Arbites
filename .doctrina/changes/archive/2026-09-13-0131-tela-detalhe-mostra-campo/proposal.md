# Change 0131-tela-detalhe-mostra-campo — tela de detalhe mostra campo vazio com o mesmo peso do preenchido e a acao destrutiva com o mesmo destaque da principal

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

tela de detalhe mostra campo vazio com o mesmo peso do preenchido e a acao destrutiva com o mesmo destaque da principal

## What

- `design-system` (spec MODIFIED): campo pelo próprio conteúdo, e a ação
  destrutiva fora do alcance de um erro de mira.
- `frontend/src/components/OverflowMenu.tsx` (novo): o menu de ações,
  reaproveitável também nas linhas de tabela.
- `frontend/src/components/ReadView.tsx` e `styles.css`: o dimensionamento
  do campo.
- `frontend/src/components/TestCaseEditor.tsx`: a ação destrutiva recolhida.

## Scope boundaries

- Não esconde campo vazio: saber que um caso não tem squad é informação. O
  que muda é o espaço que essa informação ocupa.
- Não remove nenhuma ação: excluir continua a dois cliques, com a mesma
  confirmação de sempre.
- Não reorganiza o detalhe em painel lateral, que é mudança de layout maior
  e merece decisão própria.

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
