# Tasks — Change 0170-run-local-cria-execution

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Reproduzir o arranque do subprocess com o valor relatado.
- [x] `resolver_python` com recusa explicativa e resolução de virtualenv.
- [x] `PUT /targets` recusa ao salvar, não ao executar.
- [x] O aborto fica na execution mesmo sem CT vinculado, e no índice.
- [x] A lista de runs mostra o motivo em vez de "sem resultados".
- [x] Testes cobrindo os cinco formatos de `python_path` e o aborto sem CT.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-15-0170-run-local-cria-execution/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
