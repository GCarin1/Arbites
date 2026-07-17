# Change 0070-automacao-reordenar-abas-para-historico-primeira — Automacao: reordenar abas para Historico (primeira e default) depois Executar e Configurar por ultimo; primeiro uso sem target orienta para Configurar via empty state

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** local-automation

## Why

Automacao: reordenar abas para Historico (primeira e default) depois Executar e Configurar por ultimo; primeiro uso sem target orienta para Configurar via empty state

## What

Ordem das abas da Automação vira Histórico → Executar → Configurar, com
Histórico como default. O auto-open de Configurar no primeiro uso sem
target é REMOVIDO — o empty state do Histórico orienta e aponta para
Configurar (config por último, como pedido).

## Scope boundaries

Só ordem/default e textos de orientação; nenhuma funcionalidade das
abas muda.

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
