# Tasks — Change 0002-m1-execucao-manual-executions-kanban-de-resultad

- [x] Backend: `executions.py` — criação com snapshot de steps, mutações
      (status, step, comentário), history, fechamento, regras de estado.
- [x] Backend: evidências — upload multipart, SHA-256, gravação em
      `evidences/CT-XXXX/`, remoção (trash).
- [x] Backend: defeitos — criação/edição de `.md` em `defects/`, vínculo
      com resultado (`results[].defects[]`).
- [x] Backend: indexer — scan de `executions/**/execution.json` (tabelas
      executions/results/evidences) + watcher para `.json`.
- [x] Backend: rotas M1 na API (contrato http-api).
- [x] Backend: testes — `test_executions.py`, `test_executions_e2e.py`
      (SC2: ~20 CTs + evidências + defeito), `test_defects.py`.
- [x] Frontend: aba Execuções — lista + form de criação com seleção de
      CTs `ready`.
- [x] Frontend: tela da execution — Kanban com drag nativo (6 colunas),
      card → painel com steps marcáveis, evidências e comentário.
- [x] Frontend: criação de defeito a partir de resultado failed;
      fechamento da execution.
- [x] Deltas das specs executions (verified), defects (partial — matriz é
      M1.5) e indexing (execution.json no scan).
- [x] `doctrina analyze` limpo e `doctrina verify` verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-03-0002-m1-execucao-manual-executions-kanban-de-resultad/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
