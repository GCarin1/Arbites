# Change 0125-visao-mobile-casca-app — visao mobile: a casca do app e desktop e num celular a barra lateral fixa engole a tela

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

visao mobile: a casca do app e desktop e num celular a barra lateral fixa engole a tela

## What

- `design-system` (spec MODIFIED): a casca passa a ter comportamento
  declarado em tela estreita.
- `frontend/src/App.tsx`: a gaveta de navegação e o cabeçalho enxuto.
- `frontend/src/styles.css`: o ponto de quebra único, a gaveta, a rolagem
  por bloco e os alvos de toque.
- `frontend/src/components/Executions.tsx`: o Kanban com encaixe por coluna.

## Scope boundaries

- Não é um app separado nem uma rota `/mobile`: é a mesma tela sabendo se
  encolher, com um ponto de quebra e nenhuma duplicação de componente.
- Não esconde funcionalidade: o que sai do cabeçalho em tela estreita são
  controles de administração da instância, e todos continuam alcançáveis
  pelas telas correspondentes.
- Não reescreve tabela em cartão: tabela larga rola dentro do próprio
  bloco, que é o comportamento que o design-system já usa em telas grandes.
- Não mexe em nenhuma regra de negócio nem em endpoint.

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
