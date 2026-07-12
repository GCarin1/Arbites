# Tasks — Change 0056-context-pack-get-context-pack-exporta-um-bundle

- [x] `backend/arbites/context_pack.py`: `build()` reaproveitando
      `metrics.traceability` + carregamento de corpo via frontmatter.
- [x] Endpoint `GET /context-pack` em `api.py` (422 `scope_required` sem
      epic/story/squad).
- [x] Testes `backend/tests/test_context_pack.py` (6 casos) + suíte
      completa (193/193) verde.
- [x] Frontend: `ContextPackCard` em `AiAssist.tsx`, `contextPackUrl` em
      `api.ts` (mesmo padrão de download de `todosExportUrl`).
- [x] `npm run build` limpo (typecheck + vite build).
- [x] Smoke test contra servidor real: bundle por story inclui corpo do
      CT e causa raiz/correção do defeito; sem escopo devolve 422.
- [x] Spec `context-pack` escrita (`doctrina spec new context-pack` +
      conteúdo completo).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-12-0056-context-pack-get-context-pack-exporta-um-bundle/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
