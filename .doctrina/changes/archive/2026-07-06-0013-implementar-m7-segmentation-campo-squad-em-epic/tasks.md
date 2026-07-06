# Tasks — Change 0013-implementar-m7-segmentation-campo-squad-em-epic

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Índice: colunas squad/squad_effective + `_recompute_effective_squads` (herança) no reindex completo e incremental.
- [x] API: squad nos models; filtro squad em /testcases, /requirements, /executions, /metrics/*; GET /squads.
- [x] metrics.py: parâmetro squad nas 7 métricas + matriz (recorte por squad_effective).
- [x] executions.py: squad no execution.json.
- [x] Frontend: campo squad nos editores; chip de filtro no board e no dashboard; squad na criação de execução.
- [x] Testes test_segmentation.py (6) + suíte cheia verde (73) + build do frontend.
- [x] Delta segmentation → verified (Implementation + 4 critérios).

## Closing steps

- [x] Apply the change: delta MODIFIED mesclado à spec `segmentation` à mão.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-06-0013-implementar-m7-segmentation-campo-squad-em-epic/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
