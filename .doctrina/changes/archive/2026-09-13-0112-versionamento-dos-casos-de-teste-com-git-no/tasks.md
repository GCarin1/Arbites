# Tasks — Change 0112-versionamento-dos-casos-de-teste-com-git-no

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `backend/arbites/versioning.py`: `git init` com `.gitignore` do índice, commit por ação com autor da sessão e degradação silenciosa quando o git não está disponível.
- [x] Commit nas ações de caso de teste: criar, editar (incluindo o markdown cru), mover e excluir.
- [x] Rotas `GET /testcases/{id}/versions`, `.../versions/{sha}`, `.../versions/diff` e `POST .../versions/{sha}/restore`.
- [x] Commit de autoria externa para edição feita por fora (Obsidian), antes de responder o histórico.
- [x] `backend/tests/test_versioning.py` provando os três critérios, inclusive o workspace sem git.
- [x] Aba de histórico no caso de teste: lista de versões, comparação com a atual e restauração.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0112-versionamento-dos-casos-de-teste-com-git-no/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
