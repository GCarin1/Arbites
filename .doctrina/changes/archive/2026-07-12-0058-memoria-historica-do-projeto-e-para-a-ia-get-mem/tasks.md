# Tasks — Change 0058-memoria-historica-do-projeto-e-para-a-ia-get-mem

- [x] Config `agent_event: AGT` no `DEFAULT_CONFIG` + SUBDIR `agent_log/`
      (`workspace.py`).
- [x] Indexer: tabela `agent_events`, `_insert_agent_event`, wiring em
      `reindex_full`/`reindex_file`/`_find_id` (`indexer.py`).
- [x] `backend/arbites/project_memory.py`: `timeline()` (cruza requirements/
      defects/decisions/agent_events) e `recent_recap()`.
- [x] `api.py`: `_log_agent_event`/`_with_project_recap`, wireados em
      `ai_generate`/`ai_review`/`ai_negative`; endpoint
      `GET /memory/timeline?kinds=&limit=`.
- [x] Testes `backend/tests/test_project_memory.py` (11 casos, incluindo
      prompt real via recording transport) + suíte completa (212/212) verde.
- [x] Frontend: `Memory.tsx` (timeline estilo git log, filtro por tipo,
      navegação para requisito/defeito/decisão), tipos em `types.ts`,
      client `memoryTimeline()` em `api.ts`, aba "Memória do Projeto" em
      `App.tsx`, CSS em `styles.css`.
- [x] `npm run build` limpo (typecheck + vite build).
- [x] Smoke test contra servidor real: epic + decisão + defeito com lição
      → timeline devolve os 4 eventos (requirement/defect/lesson/decision)
      corretamente; filtro `kinds=decision` restringe certo.
- [x] Spec `project-memory` escrita (`doctrina spec new project-memory` +
      conteúdo completo).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-12-0058-memoria-historica-do-projeto-e-para-a-ia-get-mem/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
