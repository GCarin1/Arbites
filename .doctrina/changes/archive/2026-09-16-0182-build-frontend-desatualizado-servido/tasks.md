# Tasks — Change 0182-build-frontend-desatualizado-servido

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Comparar a data do build com a do fonte, ignorando o que não muda o bundle.
- [x] Alertar no arranque, antes do uvicorn.
- [x] Mesmo aviso na lista de problemas da API.
- [x] Não afirmar nada quando não há o que comparar (o caso do container).
- [x] Testes, inclusive o cenário do `git pull` sem build.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-16-0182-build-frontend-desatualizado-servido/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
