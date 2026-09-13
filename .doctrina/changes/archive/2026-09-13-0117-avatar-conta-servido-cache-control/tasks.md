# Tasks — Change 0117-avatar-conta-servido-cache-control

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `Cache-Control: private, no-cache` na resposta de `GET /profile/avatar`.
- [x] Teste do cabeçalho e da troca de foto mudando o ETag em `backend/tests/test_avatar.py`.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0117-avatar-conta-servido-cache-control/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
