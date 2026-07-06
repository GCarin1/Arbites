# Tasks — Change 0009-bug-grafico-de-tendencia-do-dashboard-infla-cont

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Escrever delta de spec `reporting` (tendência por resultado líquido + unwanted-behavior).
- [x] Corrigir `metrics.trend()` para contar o status final do dia por (execução, CT) via window function.
- [x] Adicionar teste de regressão `test_trend_does_not_inflate_from_repeated_moves` (SC5).
- [x] Confirmar que `test_trend_counts_daily_events` continua verde sob a nova semântica.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-06-0009-bug-grafico-de-tendencia-do-dashboard-infla-cont/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
