# Tasks — Change 0055-agente-auditor-consolida-sinais-que-ja-existem-n

- [x] Workspace: SUBDIR `audits/` e prefixo de ID `AUD` (`workspace.py`).
- [x] Indexer: tabela `audits`, `_insert_audit`, wiring em `reindex_full`/
      `reindex_file`/`_find_id` (`indexer.py`).
- [x] `backend/arbites/audit.py`: `collect_findings` (4 categorias),
      `summarize`, `audit_markdown`.
- [x] Endpoints `POST /audit/run`, `GET /audit/latest`, `GET /audit/history`,
      `GET /audit/{id}` em `api.py` (rotas estáticas antes da dinâmica).
- [x] Testes `backend/tests/test_audit.py` (16 casos) + suíte completa
      (187/187) verde.
- [x] Frontend: `Audit.tsx`, tipos em `types.ts`, client em `api.ts`, aba
      "Auditoria" em `App.tsx`, CSS em `styles.css`.
- [x] `npm run build` limpo (typecheck + vite build).
- [x] Smoke test contra servidor real: `/audit/latest` auto-roda vazio,
      `/audit/run` manual, achado de `uncovered_story` aparece após criar
      story sem CT, `/audit/history` lista as 3 rodadas.
- [x] Spec `audit` escrita (`doctrina spec new audit` + conteúdo completo).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-12-0055-agente-auditor-consolida-sinais-que-ja-existem-n/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
