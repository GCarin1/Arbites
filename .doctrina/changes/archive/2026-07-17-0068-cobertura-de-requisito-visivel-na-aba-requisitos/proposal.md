# Change 0068-cobertura-de-requisito-visivel-na-aba-requisitos — Cobertura de requisito visivel na aba Requisitos: cada story mostra se esta coberta (>=1 CT vinculado) ou nao, com contagem de CTs; filtro sem-cobertura; o dado ja existe na matriz do Dashboard, falta na tela de Requisitos

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** requirements

## Why

Cobertura de requisito visivel na aba Requisitos: cada story mostra se esta coberta (>=1 CT vinculado) ou nao, com contagem de CTs; filtro sem-cobertura; o dado ja existe na matriz do Dashboard, falta na tela de Requisitos

## What

A tela de Requisitos (`ReqRepository`) passa a mostrar, por story, o
estado de cobertura: badge "coberta (N CTs)" ou "sem cobertura" (status-dot
do design system), mais um filtro "só sem cobertura". Epics agregam
"X/Y stories cobertas". O dado já existe (`GET /metrics/traceability` /
`GET /testcases?story=`) — é exposição na tela certa, sem métrica nova.

## Scope boundaries

Não muda o cálculo de cobertura (spec reporting intocada) nem cria
endpoint novo se a matriz já servir; no máximo um agregado leve. Não mexe
no editor de requisito.

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
