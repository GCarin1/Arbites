# Change 0104-autoria-pelo-usuario-logado — Autoria pelo usuario logado

- **Status:** proposed
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** profile

## Why

Com varios usuarios sobre o mesmo workspace, a identidade logada passa a preencher automaticamente a autoria: owner e author de executions, criador de requisitos, casos de teste e defeitos deixam de ser texto livre e passam a vir da sessao. O profile.md, hoje unico na raiz do workspace e global, passa a ser por usuario, preservando a memoria de IA individual sem vazar entre contas.

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
