# Change 0072-clareza-da-aba-decisoes-subtitle-e-texto-curto — Clareza da aba Decisoes: subtitle e texto curto de proposito (registro do porque das decisoes do projeto sob teste), empty state com exemplo; seguir o design system

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** decisions

## Why

Clareza da aba Decisoes: subtitle e texto curto de proposito (registro do porque das decisoes do projeto sob teste), empty state com exemplo; seguir o design system

## What

Aba Decisões ganha subtitle ("o porquê das escolhas do projeto sob
teste — memória de longo prazo") e o empty state passa a incluir um
exemplo concreto de decisão (genérico). Segue `.subtitle` do
design-system.

## Scope boundaries

Nenhuma mudança de backend. Não confundir com os ADRs do framework
Doctrina (nota já existe no código).

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

<!-- List unresolved decisions. Empty if none. -->
