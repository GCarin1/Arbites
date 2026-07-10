# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

## Context

Doc de ajustes §1.5.2: o disparo remoto (workflow corporativo) aceita os
parâmetros arquivo `.feature`, tag do Behave, ambiente (dev|cer|prd),
navegador e repositório de origem, repassados como `inputs` do
workflow_dispatch quando informados.

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall aceitar em `POST /runs/ci` os parâmetros opcionais
  `feature`, `environment (dev|cer|prd)`, `browser` e `source_repo`,
  repassando-os como inputs do workflow_dispatch quando informados.

## Acceptance criteria (ADDED)

4. [verified] Inputs opcionais do dispatch (feature/environment/browser/
   source_repo) chegam ao workflow — verified by `backend/tests/test_ci_runs.py`.
