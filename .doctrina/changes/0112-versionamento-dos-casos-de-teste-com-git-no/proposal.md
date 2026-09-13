# Change 0112-versionamento-dos-casos-de-teste-com-git-no — Versionamento dos casos de teste com git no workspace

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** testcases

## Why

Transformar o workspace num repositorio git de verdade: init automatico e commit por acao semantica da interface, assinado com o autor da sessao, em vez de um commit por gravacao. Historico, comparacao entre versoes e restauracao expostos numa aba do proprio caso de teste. Edicao feita por fora, no Obsidian, tambem vira commit, com autoria externa.

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
