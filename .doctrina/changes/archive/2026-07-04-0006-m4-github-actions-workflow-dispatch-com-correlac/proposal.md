# Change 0006-m4-github-actions-workflow-dispatch-com-correlac — M4 - GitHub Actions: workflow_dispatch com correlacao de run, polling de status, coleta de artifact Cucumber JSON, PAT no keyring, tests.yml de exemplo

- **Status:** proposed
- **Date:** 2026-07-04
- **Owner:** Gcarini
- **Affects specs:** ci-automation

## Why

M4 é o quinto passo da ordem de entrega: disparar o workflow real pela UI,
acompanhar os steps do workflow e, ao fim, ter a execution idêntica à de
um run local (SC6). Design respeita a restrição real da API do GitHub
(ADR 0006): logs de job só após o término → coleta por artifact com o
mesmo parser Cucumber JSON do M3.

## What

- `backend/arbites/ci.py` — cliente GitHub Actions atrás de uma interface
  injetável (`GitHubClient`): dispatch (`workflow_dispatch`), correlação
  do run (mais recente pós-dispatch, janela 30 s, `event:
  workflow_dispatch`), status consolidado (run + jobs + steps), download
  de artifact com backoff em rate limit. Implementação real via httpx; os
  testes usam um fake em memória (a API do GitHub não é acessível no
  gate).
- Token: PAT fine-grained via `keyring` no cofre do SO — nunca em YAML,
  nunca no índice, nunca logado; `GET /settings/github/token` retorna só
  o status.
- Coleta: extrai o Cucumber JSON + screenshots do zip do artifact e
  popula a execution `origin: github_actions` com o MESMO adapter
  `behave_json` do run local; objeto `ci {workflow_run_id, run_url,
  commit_sha, artifact_id}` preenchido.
- API M4: `POST /runs/ci`, `GET /runs/ci/{exec_id}/status`,
  `POST /runs/ci/{exec_id}/collect`, `GET/PUT /settings/github/token`.
- `docs/examples/tests.yml` — workflow de exemplo (workflow_dispatch com
  input de tags + publicação do artifact).
- Frontend: painel CI na aba Automação (dispatch, timeline de steps do
  workflow, collect) + settings do token.
- Testes: `backend/tests/test_ci_runs.py` (fake client: dispatch →
  correlação → status → collect com zip real de artifact),
  `test_ci_token.py` (keyring fake; valor nunca exposto).

## Scope boundaries

- Self-hosted runner: fora da v1 (alternativa registrada no ADR 0006; a
  coleta por artifact funciona igual).
- Teste contra a API real do GitHub: fora do gate (exige rede/segredo);
  o cliente real é fino e o contrato está no fake + shapes fixados.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
