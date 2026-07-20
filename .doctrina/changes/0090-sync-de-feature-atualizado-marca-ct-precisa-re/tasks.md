# Tasks — Change 0090-sync-de-feature-atualizado-marca-ct-precisa-re

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [ ] `feature_sync` apply(update): grava `needs_rerun: true` no CT.
- [ ] Limpeza do flag ao registrar resultado do CT (exec_ops/set_result_status).
- [ ] Indexer + filtro `needs_rerun` em GET /testcases; badge na UI.
- [ ] Testes + `npm run build`.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-19-0090-sync-de-feature-atualizado-marca-ct-precisa-re/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
