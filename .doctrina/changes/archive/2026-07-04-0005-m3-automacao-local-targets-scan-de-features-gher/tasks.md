# Tasks — Change 0005-m3-automacao-local-targets-scan-de-features-gher

- [x] Backend: `gherkin_scan.py` (pacote oficial, `# language: pt`,
      mapa `@CT-XXXX`, warnings órfão/quebrada/duplicada) + integração no
      reindex_full e `POST /targets/{name}/scan`.
- [x] Backend: `behave_json.py` — adapter Cucumber JSON → resultados
      neutros, fixtures de contrato versionadas.
- [x] Backend: `runner.py` — fila FIFO por target, subprocess assíncrono,
      timeout → blocked, buffer + SSE, evidências movidas/hasheadas,
      execution `local_run`.
- [x] Backend: rotas `GET /targets`, `POST /targets/{name}/scan`,
      `POST /runs/local`, `GET /runs/{exec_id}/stream`,
      `POST /runs/{exec_id}/cancel`.
- [x] Docs: `docs/examples/environment.py` (contrato de evidências).
- [x] Backend: fixture mini-repo Behave (pt) + `test_gherkin.py` +
      `test_local_runs.py` (E2E com behave real).
- [x] Frontend: aba Automação — targets, run local, log SSE, fila, cancel.
- [x] Deltas: local-automation → verified; indexing → verified (critério
      Gherkin fechado).
- [x] `doctrina analyze` limpo e `doctrina verify` verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-04-0005-m3-automacao-local-targets-scan-de-features-gher/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
