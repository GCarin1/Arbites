# Tasks — Change 0006-m4-github-actions-workflow-dispatch-com-correlac

- [x] Backend: `ci.py` — TokenStore (keyring), GitHubClient (httpx real +
      interface p/ fake), CIManager (dispatch, correlação 30 s, status
      consolidado, collect via zip + behave_json).
- [x] Backend: rotas `POST /runs/ci`, `GET /runs/ci/{exec_id}/status`,
      `POST /runs/ci/{exec_id}/collect`, `GET/PUT /settings/github/token`.
- [x] Docs: `docs/examples/tests.yml` (workflow_dispatch + artifact).
- [x] Backend: `test_ci_runs.py` (fake client, zip real) e
      `test_ci_token.py` (keyring fake, valor nunca exposto).
- [x] Frontend: painel CI na aba Automação + settings do token.
- [x] Delta: ci-automation → verified.
- [x] `doctrina analyze` limpo e `doctrina verify` verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-04-0006-m4-github-actions-workflow-dispatch-com-correlac/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
