# Change 0111-execution-como-ciclo-de-teste — Execution como ciclo de teste

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

Dar ao ciclo a estrutura que hoje falta: sprint deixa de ser texto livre e passa a ter datas de inicio e fim e status de ciclo entre planejado, em andamento e fechado, o que substitui a decisao registrada na ADR 0010. Cabecalho de progresso no padrao do Xray, com barra empilhada por status, contadores grandes e total de casos. Responsavel por caso de teste dentro do ciclo, para dividir uma regressao entre varias pessoas, aproveitando a autoria por sessao que ja existe.

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
