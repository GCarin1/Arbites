# Contract — http-api

**Contract:** http-api
**Status:** active
**Last updated:** 2026-07-03

## Purpose

O seam entre a React SPA (Vite) e o backend FastAPI. Possui a base URL, o
formato de erro, o versionamento do path e o mapa de rotas por milestone.
Em produção local o próprio FastAPI serve o build da SPA como estático (um
processo, um comando); em desenvolvimento a SPA roda no dev server do Vite
apontando para a mesma base URL.

## Ports

| Service | Port | Protocol |
|---------|------|----------|
| arbites-backend (uvicorn: API + SPA estática) | 8347 | http |
| vite-dev (apenas desenvolvimento) | 5173 | http |

## Environment

| Variable | Required | Example |
|----------|----------|---------|
| ARBITES_WORKSPACE | yes | D:/qa/workspace |
| ARBITES_EVIDENCE_DIR | no (injetada pelo backend nos runs locais) | C:/tmp/arbites-run-42/evidences |

## Interfaces

- Base URL: `http://localhost:8347/api/v1`.
- Erros: `{ "error": { "code": "...", "message": "..." } }`.
- Toda resposta de escrita retorna a entidade atualizada.
- Rotas por milestone (contrato completo no intake §8):
  - M0: `/workspace`, `/workspace/reindex`, `/warnings`, `/tree`,
    `/requirements[...]`, `/testcases[...]` (+ `/{id}/raw`).
  - M1: `/executions[...]`, `/executions/{id}/results/{ct}/status|steps|evidences`,
    `/executions/{id}/close`, `/defects[...]`.
  - M1.5: `/metrics/summary|trend|coverage|traceability|flaky`.
  - M2: `/import/xray`, `/import/xray/confirm`, `/export/markdown`.
  - M3: `/targets`, `/targets/{name}/scan`, `/runs/local`,
    `/runs/{exec_id}/stream` (SSE), `/runs/{exec_id}/cancel`.
  - M4: `/runs/ci`, `/runs/ci/{exec_id}/status`, `/runs/ci/{exec_id}/collect`,
    `/settings/github/token`.
  - M5: `/ai/providers`, `/ai/generate-testcases`, `/ai/review/{id}`,
    `/ai/negative-cases/{id}`.
- Streaming: `GET /runs/{exec_id}/stream` é SSE (stdout + eventos de step
  em tempo real); único endpoint não-JSON-request/response da v1.
- Upload de evidência: multipart em
  `POST /executions/{id}/results/{ct}/evidences`; o backend grava no disco
  e calcula SHA-256.
- `GET /settings/github/token` retorna apenas status (nunca o valor).

## References

- `specs/workspace-core`
- `specs/indexing`
- `specs/requirements`
- `specs/testcases`
- `specs/executions`
- `specs/defects`
- `specs/reporting`
- `specs/xray-migration`
- `specs/local-automation`
- `specs/ci-automation`
- `specs/ai-assist`
