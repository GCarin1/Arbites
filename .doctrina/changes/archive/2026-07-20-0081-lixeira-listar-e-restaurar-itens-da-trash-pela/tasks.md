# Tasks — Change 0081-lixeira-listar-e-restaurar-itens-da-trash-pela

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `workspace.py`: `trash()` registra origem; helpers `list_trash`/`restore`/`empty`.
- [x] API: `GET /trash`, `POST /trash/{name}/restore` (+reindex), `DELETE /trash`.
- [x] UI: lista com nome/tipo/data, Restaurar (toast) e Esvaziar (ConfirmModal).
- [x] Testes `test_trash.py` + `npm run build`.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-19-0081-lixeira-listar-e-restaurar-itens-da-trash-pela/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
