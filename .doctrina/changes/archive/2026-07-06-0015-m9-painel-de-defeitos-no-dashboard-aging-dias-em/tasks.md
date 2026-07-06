# Tasks — Change 0015-m9-painel-de-defeitos-no-dashboard-aging-dias-em

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] indexer: coluna opened_at + índice do `opened`.
- [x] api: carimbar opened na criação; GET /metrics/defects.
- [x] metrics: defects_report (aging/severidade/squad + lista).
- [x] frontend: DefectsPanel no dashboard com filtro de squad.
- [x] testes de defeitos + suíte cheia (77) + build.
- [x] deltas defects (opened+report) e reporting (endpoint+painel) → verified.

## Closing steps

- [x] Apply the change: deltas MODIFIED (defects, reporting) mesclados à mão.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-06-0015-m9-painel-de-defeitos-no-dashboard-aging-dias-em/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
