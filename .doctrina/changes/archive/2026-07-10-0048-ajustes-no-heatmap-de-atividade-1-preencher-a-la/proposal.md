# Change 0048-ajustes-no-heatmap-de-atividade-1-preencher-a-la — ajustes no heatmap de atividade: (1) preencher a largura do card (colunas flexiveis + celulas com aspect-ratio, escalam com o card em vez de 11px fixos), (2) filtro por ano (GET /metrics/activity aceita year; resposta lista os anos com atividade para o seletor), (3) tooltip flutuante no cursor mostrando quantas mudancas houve no dia + breakdown

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** reporting

## Why

ajustes no heatmap de atividade: (1) preencher a largura do card (colunas flexiveis + celulas com aspect-ratio, escalam com o card em vez de 11px fixos), (2) filtro por ano (GET /metrics/activity aceita year; resposta lista os anos com atividade para o seletor), (3) tooltip flutuante no cursor mostrando quantas mudancas houve no dia + breakdown

## What

Ajustes pedidos no heatmap de atividade (change 0047):

- **Preenche o card:** o CSS troca células de 11px fixos por grade flexível —
  colunas `flex:1` e células `aspect-ratio:1/1` que escalam com a largura do
  card (card maior = quadrados maiores). Rótulos de mês/dia acompanham como
  irmãos flex, mantendo o alinhamento.
- **Filtro por ano:** `GET /metrics/activity` aceita `year` (janela do ano
  civil alinhada à segunda); a resposta lista `years` (anos com atividade)
  para o seletor. `metrics._activity_years` computa os anos.
- **Tooltip no cursor:** ao passar o mouse numa célula, um tooltip flutuante
  (`position:fixed` no clientX/clientY — evita o offset do ancestral
  `position:relative`) mostra "N mudanças em DD/MM/AAAA" + o detalhamento
  (execuções/bugs/CTs/requisitos/runs).

Arquivos: `backend/arbites/metrics.py`, `backend/arbites/api.py`,
`frontend/src/components/ActivityHeatmap.tsx`, `frontend/src/styles.css`.
`reporting` spec MODIFIED (delta) + critério [verified] #11.

## Scope boundaries

- `aspect-ratio` e `color-mix` exigem navegador moderno (o app já é Vite/React
  evergreen) — sem fallback para browsers antigos.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (152 testes backend + build frontend).
- [x] Critério #11 do reporting cita `backend/tests/test_activity_heatmap.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
