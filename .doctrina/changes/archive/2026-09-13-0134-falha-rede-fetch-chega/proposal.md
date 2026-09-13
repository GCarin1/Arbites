# Change 0134-falha-rede-fetch-chega — falha de rede no fetch chega a tela como Failed to fetch em ingles sem dizer o que fazer

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

falha de rede no fetch chega a tela como Failed to fetch em ingles sem dizer o que fazer

## What

- `design-system` (spec MODIFIED): falha de rede é um estado próprio, com
  mensagem própria.
- `frontend/src/api.ts`: um só lugar traduz a rejeição do `fetch`, usado
  pelo cliente e pelos quatro envios de arquivo.

## Scope boundaries

- Não mexe na mensagem que vem do servidor: quando ele responde, a mensagem
  dele já está certa e continua sendo exibida.
- Não tenta reenviar sozinho: repetir uma requisição que falhou sem a pessoa
  pedir esconde o problema em vez de mostrá-lo.
- Não diagnostica a causa da falha de rede, que o navegador não informa.

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
