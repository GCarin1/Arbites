# Tasks — Change 0099-local-automation-correcoes-de-execucao-injetar-o

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Runner: helper `load_env_file` + mesclar o `.env` do target no env do subprocess (sem sobrescrever `ARBITES_*`/`PYTHONIOENCODING`).
- [x] Catálogo derivado: `GET /env/catalog?target=` lê chaves/seções de `.env` + `.env.example` do target; remover `ENV_CATALOG` fixo.
- [x] Testes backend: run injeta `.env`; catálogo deriva do projeto.
- [x] Frontend: reconectar ao run ativo no mount (replay do stream) — terminal não some ao voltar.
- [x] Frontend: `Run EXEC-XXXX` navegável ao board; feature-picker com "selecionar todos/limpar" + vazio explicado.
- [x] `npm run build` + revisão visual.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-21-0099-local-automation-correcoes-de-execucao-injetar-o/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
