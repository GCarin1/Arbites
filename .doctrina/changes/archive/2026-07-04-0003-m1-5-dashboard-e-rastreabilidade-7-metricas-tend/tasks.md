# Tasks — Change 0003-m1-5-dashboard-e-rastreabilidade-7-metricas-tend

- [x] Indexer: tabela `result_events` populada do `history[]` no scan de
      execution.json.
- [x] Backend: `metrics.py` — 7 métricas com numerador/denominador
      explícitos + matriz de rastreabilidade + trend.
- [x] Backend: rotas `GET /metrics/summary|trend|coverage|traceability|flaky`.
- [x] Backend: export da matriz em Markdown e PDF (fpdf2) + download de
      arquivo de evidência.
- [x] Backend: testes — `test_metrics.py` (fórmulas em dataset fixo),
      `test_export.py` (MD/PDF), `test_reporting_e2e.py` (SC3 com
      drill-down até evidência).
- [x] Frontend: aba Dashboard — cards de métricas com fórmula visível,
      tendência (recharts), filtros sprint/período.
- [x] Frontend: matriz navegável (epic → story → últimos resultados →
      evidência baixável) + botões export MD/PDF.
- [x] Deltas: reporting → verified; defects → verified (critério da
      matriz agora tem teste).
- [x] `doctrina analyze` limpo e `doctrina verify` verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-04-0003-m1-5-dashboard-e-rastreabilidade-7-metricas-tend/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
