# Change 0128-tema-claro-opcional-cores — tema claro opcional com as cores dos graficos saindo de valores cravados para tokens

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

tema claro opcional com as cores dos graficos saindo de valores cravados para tokens

## What

- `design-system` (spec MODIFIED): cor sempre de token, e tema claro como
  escolha de quem lê.
- `frontend/src/components/Dashboard.tsx` e `Automation.tsx`: as dez cores
  cravadas passam a vir dos tokens.
- `frontend/src/theme.ts` (novo): a escolha, a preferência do sistema e a
  aplicação antes da primeira pintura.
- `frontend/src/styles.css`: a paleta clara como variante.
- `frontend/src/components/Profile.tsx`: o seletor, ao lado da densidade.

## Scope boundaries

- Não troca o padrão do produto: o escuro continua sendo o ponto de partida
  e a identidade da ferramenta.
- Não redesenha nada: o tema claro reusa a mesma estrutura, os mesmos
  componentes e os mesmos papéis de cor.
- Não guarda o tema no workspace: como a densidade, é de quem lê num
  aparelho.

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
