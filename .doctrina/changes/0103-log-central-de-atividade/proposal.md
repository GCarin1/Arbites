# Change 0103-log-central-de-atividade — Log central de atividade

- **Status:** proposed
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (uncertain; signals: requisito)
- **Affects specs:** audit

## Why

Log central de escrita respondendo quem fez o que e quando: criacao, edicao e exclusao de requisito, caso de teste, execution e defeito, disparo de automacao, alteracao de .env e de token. Cada entrada guarda usuario, acao, alvo, data e IP; a consulta e paginada e filtravel por usuario, acao e periodo, exposta ao papel admin e alimentando a aba Atividade do painel. Reaproveita o padrao de eventos que ja existe no historico das executions.

## What

<!-- The shape of the change: artifacts created or modified, specs affected. -->

## Scope boundaries

<!-- Anything adjacent that this change deliberately does NOT touch. -->

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
