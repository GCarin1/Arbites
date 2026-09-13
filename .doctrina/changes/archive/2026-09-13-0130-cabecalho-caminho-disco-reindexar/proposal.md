# Change 0130-cabecalho-caminho-disco-reindexar — cabecalho com caminho do disco e reindexar competindo, e botao orfao acima do titulo em execucoes

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

cabecalho com caminho do disco e reindexar competindo, e botao orfao acima do titulo em execucoes

## What

- `design-system` (spec MODIFIED): o que a barra superior carrega, e onde
  ficam as ações de uma tela.
- `frontend/src/App.tsx`: o caminho vira dica, reindexar vira ação
  discreta, e o botão do modo guiado entra no cabeçalho da tela.
- `frontend/src/components/NavIcons.tsx`: o ícone de reindexar.

## Scope boundaries

- Não remove nada do alcance: o caminho fica a um passar de mouse e
  reindexar continua a um clique.
- Não acrescenta o botão de criar que o padrão de mercado sugere: seria
  funcionalidade nova, não revitalização, e merece decisão própria.
- Não mexe na busca nem no menu da conta.

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
