# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

M4 implementa a capability. O gate prova a orquestração com um fake do
GitHub (a API real exige rede/PAT, fora do gate); o cliente real é uma
casca fina httpx (1 método ≈ 1 endpoint REST) com backoff em rate limit.
Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — deferido ao M4 (após M3)` para
   `verified — M4 (backend/arbites/ci.py,
   frontend/src/components/Automation.tsx, docs/examples/tests.yml);
   orquestração provada com fake client — validação contra a API real
   pendente do primeiro uso com o repo da B3`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-04`.
3. Acceptance criteria:

   1. [verified] Disparo pela UI cria execution `github_actions` e
      correlaciona o run id — verified by `backend/tests/test_ci_runs.py`.
   2. [verified] Ao completar, collect produz execution idêntica em
      estrutura à de um run local — verified by
      `backend/tests/test_ci_runs.py`.
   3. [verified] Token gravado via API está no keyring e nunca aparece em
      respostas, logs ou arquivos do workspace — verified by
      `backend/tests/test_ci_token.py`.

Sem mudança nos requisitos EARS.
