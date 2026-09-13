# Tasks — Change 0090-sync-de-feature-atualizado-marca-ct-precisa-re

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `feature_sync` apply(update): grava `needs_rerun: true` no CT.
- [x] Limpeza do flag ao registrar resultado do CT (exec_ops/set_result_status).
- [x] Indexer + filtro `needs_rerun` em GET /testcases; badge na UI.
- [x] Testes + `npm run build`.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-19-0090-sync-de-feature-atualizado-marca-ct-precisa-re/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
