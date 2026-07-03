# Spec — ci-automation

**Capability:** ci-automation
**Status:** active
**Implementation:** planned — deferido ao M4 (após M3)
**Realizes:** SC6
**Last updated:** 2026-07-03
**Version:** 0.1.0

## Purpose

Dispara e acompanha runs no GitHub Actions (workflow_dispatch), coletando o
artifact com Cucumber JSON ao término para popular a execution com o mesmo
parser do run local. Design assume a restrição real da API do GitHub: logs
completos de job só existem após o término; ao vivo há apenas status de
workflow/jobs/steps do workflow.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `POST /runs/ci`, `GET /runs/ci/{exec_id}/status`,
  `POST /runs/ci/{exec_id}/collect`, `GET/PUT /settings/github/token`.
- The system shall disparar via
  `POST /repos/{repo}/actions/workflows/{workflow}/dispatches` com `ref` e
  `inputs` (ex.: tags), criando execution `origin: github_actions` com
  objeto `ci {workflow_run_id, run_url, commit_sha, artifact_id}`.
- The system shall correlacionar o run buscando o run mais recente do
  workflow criado após o dispatch (janela de 30 s, filtro
  `event: workflow_dispatch`), pois a API não retorna o run id.
- The system shall armazenar o PAT fine-grained (escopo mínimo
  `actions:read+write` no repo do target) exclusivamente via `keyring` no
  cofre do SO.
- The system shall reutilizar na coleta o mesmo parser de Cucumber JSON do
  run local, movendo evidências do artifact para `evidences/`.
- The system shall documentar um `tests.yml` de exemplo: o workflow deve
  aceitar `workflow_dispatch` com input de tags e publicar JSON +
  screenshots como artifact.

### Event-driven

- When um run CI está em andamento, the system shall fazer polling a cada
  10 s em `/actions/runs/{id}` e `/actions/runs/{id}/jobs`, exibindo a
  timeline dos steps do workflow (`queued → in_progress → completed`).
- When o workflow completa, the system shall baixar o artifact configurado
  (`artifact_name`), extrair o Cucumber JSON, parsear e popular
  `results[]`.
- When a API do GitHub retorna rate limit, the system shall aplicar
  backoff no polling.

### State-driven

- While o job está em andamento, the system shall exibir apenas o status
  dos steps do workflow (não dos steps Gherkin — indisponíveis ao vivo).

### Unwanted-behavior (must-not)

- The system shall not gravar o PAT em YAML, no índice ou em logs.
- The system shall not retornar o valor do token em
  `GET /settings/github/token` (status apenas).

### Optional

- Where um self-hosted runner local é usado (alternativa registrada em
  ADR), the system may coletar pelo mesmo mecanismo de artifact sem
  mudança de design.

## Acceptance criteria

1. [unverified] Disparo real pela UI cria execution `github_actions` e
   correlaciona o run id — verified by `tests/test_ci_runs.py`.
2. [unverified] Ao completar, collect produz execution idêntica em
   estrutura à de um run local — verified by `tests/test_ci_runs.py`.
3. [unverified] Token gravado via API está no keyring e nunca aparece em
   respostas ou logs — verified by `tests/test_ci_token.py`.

## Maturity

**MVP (committed):**

- workflow_dispatch, correlação, polling com timeline, coleta de artifact,
  PAT no keyring, `tests.yml` de exemplo.

**Future (aspirational, not committed):**

- Self-hosted runner na máquina local (registrado como alternativa em
  ADR; não entra na v1).

## Out of scope for this spec

- Execução local (ver `local-automation`).
