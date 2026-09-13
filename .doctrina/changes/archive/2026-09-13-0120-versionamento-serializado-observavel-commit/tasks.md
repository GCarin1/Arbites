# Tasks — Change 0120-versionamento-serializado-observavel-commit

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Fila única por processo em volta das operações de git no `versioning.py`.
- [x] Aviso no log quando um commit não acontece, com a ação e o motivo.
- [x] Chamadas de git fora do event loop, pelo mesmo `asyncio.to_thread` que a casa já usa.
- [x] `backend/tests/test_versioning.py`: doze gravações simultâneas geram doze commits; falha do git vira aviso.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0120-versionamento-serializado-observavel-commit/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
