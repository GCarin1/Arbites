# Change 0098-reporte-executivo-narrado-pela-ia — reporte executivo narrado pela IA

- **Status:** applied
- **Applied:** 2026-07-21
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** reporting

## Why

O dashboard exporta números (PDF/MD); falta o parágrafo executivo que o
gestor lê primeiro. Os dados (métricas, defeitos, cobertura) já estão todos
no índice.

## What

- Backend: `POST /ai/executive-summary` (filtros sprint/squad) — envia à
  IA as 7 métricas + defeitos abertos/aging + cobertura → 2-3 parágrafos
  executivos (síntese, riscos, recomendação) — preview.
- UI: no Dashboard, "Gerar resumo executivo (IA)" com preview editável;
  incluir no export PDF/MD como seção inicial.
- Sem provider: botão oculto (dashboard 100% funcional sem IA).

## Scope boundaries

- O resumo NUNCA inventa número: o prompt injeta os valores e o preview
  é editável antes do export.
- Sem agendamento/envio automático.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Endpoint devolve resumo com os números injetados; export inclui a seção quando aceita — `backend/tests/test_reporting_summary.py` (MockTransport).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
