# Tasks — Change 0121-excluir-mover-pasta-restaurar

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Commit ao excluir pasta, com os casos afetados na ação.
- [x] Commit ao mover pasta, com as duas pontas no mesmo commit (para o `--follow` enxergar a renomeação).
- [x] Commit ao restaurar da lixeira, com o que voltou.
- [x] `backend/tests/test_versioning.py`: repositório sem pendência depois das três ações e histórico contínuo.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0121-excluir-mover-pasta-restaurar/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
