# Change 0126-escala-espacamento-valores-abaixo — escala de espacamento sem valores abaixo de oito forca numeros magicos e nao ha controle de densidade

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

escala de espacamento sem valores abaixo de oito forca numeros magicos e nao ha controle de densidade

## What

- `design-system` (spec MODIFIED): os degraus que faltavam na escala e as
  três densidades de leitura.
- `frontend/src/styles.css`: `--s0`/`--s1h`, os tokens de densidade e o
  respiro aplicado às superfícies de linha.
- `frontend/src/components/Profile.tsx`: o seletor, por ser preferência
  pessoal de leitura.
- `frontend/src/main.tsx`: aplicar a densidade guardada antes da primeira
  pintura, para a tela não piscar na densidade errada.

## Scope boundaries

- Não mexe na separação entre seções (`--s3`, `--s4`): ela é estrutura, e
  encolhê-la não faz caber mais nada, só embaralha a leitura.
- Não muda tamanho de fonte por densidade — texto menor não é o mesmo que
  interface mais densa, e mexer na fonte cobraria legibilidade.
- Não troca os 87 valores mágicos de uma vez: entram os degraus e os usos
  mais repetidos; o resto migra quando o componente for tocado.
- Não guarda a densidade no perfil do workspace: é preferência de leitura
  de uma pessoa num aparelho.

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
