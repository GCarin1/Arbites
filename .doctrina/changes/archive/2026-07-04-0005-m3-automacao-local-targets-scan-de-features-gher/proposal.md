# Change 0005-m3-automacao-local-targets-scan-de-features-gher — M3 - automacao local: targets, scan de features Gherkin, runs Behave via subprocess com SSE, fila por target, timeout, parse do JSON, evidencias via hooks

- **Status:** proposed
- **Date:** 2026-07-04
- **Owner:** Gcarini
- **Affects specs:** local-automation, indexing

## Why

M3 é o quarto passo da ordem de entrega: disparar a automação real
(Selenium + Behave) pela UI, com log ao vivo e a execution populada com
steps Gherkin e screenshots de falha (SC5). Também fecha o critério
pendente da spec indexing (parse Gherkin `# language: pt` + mapa
`@CT-XXXX`).

## What

- `backend/arbites/gherkin_scan.py` — scan dos `features_glob` de cada
  target com o pacote oficial `gherkin` (resolve `# language:`
  nativamente); popula a tabela `scenarios` e os warnings do reindex
  (cenário órfão, automação quebrada, tag duplicada).
- `backend/arbites/behave_json.py` — adapter do Cucumber JSON do Behave
  (compartilhado com o M4), com JSONs de exemplo versionados (risco §17).
- `backend/arbites/runner.py` — runs locais: `asyncio.create_subprocess_exec`,
  lock + fila FIFO por target, timeout configurável (default 30 min →
  pendentes viram `blocked` com `error: "timeout"`), stdout em buffer +
  SSE, `ARBITES_EVIDENCE_DIR` injetada, evidências movidas e hasheadas,
  execution `origin: local_run` populada pelo parser.
- API M3: `GET /targets`, `POST /targets/{name}/scan`, `POST /runs/local`,
  `GET /runs/{exec_id}/stream` (SSE), `POST /runs/{exec_id}/cancel`.
- Snippet documentado do `environment.py` (contrato de evidências) em
  `docs/examples/environment.py`.
- Frontend: aba Automação — targets, formulário de run (tags/CTs), log ao
  vivo via EventSource, fila visível, cancel.
- Testes E2E com **behave real** contra um mini-repo de automação fixture
  (features em pt com `@CT-XXXX`): `backend/tests/test_gherkin.py`,
  `test_local_runs.py`.

## Scope boundaries

- Nenhuma escrita no repo de automação (read-only — invariante).
- Runner é só Behave na v1; outros runners ficam atrás do mesmo adapter
  (Future da spec).
- GitHub Actions é o change seguinte (M4).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
