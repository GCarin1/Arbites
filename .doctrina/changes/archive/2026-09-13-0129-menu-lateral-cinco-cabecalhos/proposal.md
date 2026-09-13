# Change 0129-menu-lateral-cinco-cabecalhos — menu lateral com cinco cabecalhos para doze itens sem icone e com navegacao duplicada no avatar

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

menu lateral com cinco cabecalhos para doze itens sem icone e com navegacao duplicada no avatar

## What

- `design-system` (spec MODIFIED): ícone em todo item, grupo só onde
  esclarece, e rodapé ancorado para o que é de manutenção.
- `frontend/src/components/NavIcons.tsx` (novo): os ícones, desenhados no
  projeto.
- `frontend/src/App.tsx`: o reagrupamento e o rodapé da navegação.
- `frontend/src/styles.css`: o peso dos cabeçalhos, o alinhamento com
  ícone e a régua do rodapé.

## Scope boundaries

- Não tira nenhuma tela do alcance: o que sai do menu lateral continua no
  menu da conta e no endereço direto.
- Não traz biblioteca de ícones: são dezessete desenhos de 16px, e uma
  dependência inteira para eles cobra mais do que entrega.
- Não mexe no grupo "Mais", que existe para manter as capabilities
  congeladas fora do caminho (ADR 0012).
- Não mexe no acesso rápido por fixação, que é escolha de cada pessoa.

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
