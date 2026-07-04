# Change 0003-m1-5-dashboard-e-rastreabilidade-7-metricas-tend — M1.5 - dashboard e rastreabilidade: 7 metricas, tendencia, matriz de rastreabilidade navegavel, export PDF e Markdown

- **Status:** proposed
- **Date:** 2026-07-04
- **Owner:** Gcarini
- **Affects specs:** reporting, defects

## Why

M1.5 é a terceira etapa da ordem de entrega (product.md): o reporte para
cima é a dor declarada número um. Critério de pronto = SC3: gerar um
reporte de sprint apresentável a um gestor em menos de 1 minuto, com
drill-down até o arquivo de evidência.

## What

- `backend/arbites/metrics.py` — as 7 métricas com as fórmulas do intake
  §11 (cobertura de requisito, cobertura de execução, pass rate, taxa de
  bloqueio, retrabalho, flaky, tendência) e a matriz de rastreabilidade
  Epic → Story | CTs | Último resultado | Execution | Evidências | Defeitos.
- Indexer: nova tabela `result_events` (histórico de transições de
  resultado, parseado de `history[]`) — base para retrabalho, flaky e
  tendência por data real.
- API M1.5: `GET /metrics/summary|trend|coverage|traceability|flaky` +
  export da matriz em Markdown e PDF + download do arquivo de evidência
  (drill-down completo).
- Frontend: aba Dashboard — cards das métricas, tendência (recharts),
  matriz navegável (epic → story → CT → execution → evidência) e botões
  de export.
- Testes: `backend/tests/test_metrics.py` (fórmulas sobre dataset
  conhecido), `test_export.py` (MD/PDF), `test_reporting_e2e.py` (SC3).

## Scope boundaries

- Filtro `target` do pass rate fica para o M3 (targets ainda não existem).
- Sem comparação entre sprints nem thresholds (Future da spec reporting).
- Export é da matriz (a tela principal para chefia), não do dashboard
  inteiro.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
