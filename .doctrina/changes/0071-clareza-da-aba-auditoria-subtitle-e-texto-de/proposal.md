# Change 0071-clareza-da-aba-auditoria-subtitle-e-texto-de — Clareza da aba Auditoria: subtitle e texto de proposito (o que o auditor consolida e quando roda), legenda de severidades, empty state instrutivo; seguir o design system

- **Status:** proposed
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** audit

## Why

Clareza da aba Auditoria: subtitle e texto de proposito (o que o auditor consolida e quando roda), legenda de severidades, empty state instrutivo; seguir o design system

## What

Aba Auditoria ganha: subtitle sob o título ("verificação automática de
pendências do workspace"), um parágrafo curto de propósito no topo (o que
o auditor consolida: warnings de indexação, stories sem CT, defeitos
esquecidos, automação quebrada; roda sob demanda ou a cada 24h), legenda
das severidades (bad/warn/info com status-dot) e empty state que explica o
que significaria ter achados. Segue `.subtitle` e a gramática do
design-system.

## Scope boundaries

Nenhuma mudança de backend/contrato — só apresentação e texto. Ajuda
curta (1 linha + legenda), não parágrafos longos (skill
estados-de-feedback).

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
