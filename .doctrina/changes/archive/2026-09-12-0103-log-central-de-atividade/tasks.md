# Tasks — Change 0103-log-central-de-atividade

- [x] `auth.py`: tabela `activity` no banco durável, com índice por data e por autor.
- [x] `auth.py`: `record_activity` e `list_activity` com filtro por autor, caminho e intervalo de datas.
- [x] `api.py`: registrar no gate, após a resposta, toda escrita com status < 400 — sem lista de rotas mantida à mão.
- [x] `api.py`: `GET /admin/activity` paginado e filtrável.
- [x] `frontend`: aba Atividade no painel, com filtro por autor e por caminho.
- [x] `backend/tests/test_activity_log.py` cobrindo os 4 critérios.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0103-log-central-de-atividade/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
