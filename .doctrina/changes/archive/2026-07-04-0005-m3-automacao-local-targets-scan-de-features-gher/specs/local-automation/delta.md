# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

M3 implementa a capability. Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — deferido ao M3 (após M2)` para
   `verified — M3 (backend/arbites/runner.py, backend/arbites/gherkin_scan.py,
   backend/arbites/behave_json.py, frontend/src/components/Automation.tsx)`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-04`.
3. Acceptance criteria — todos comprovados com behave real:

   1. [verified] Disparar automação real pela UI mostra log ao vivo e
      popula a execution com steps Gherkin — verified by
      `backend/tests/test_local_runs.py`.
   2. [verified] Dois runs no mesmo target entram em fila FIFO — verified
      by `backend/tests/test_local_runs.py`.
   3. [verified] Timeout marca pendentes como `blocked` com
      `error: "timeout"` — verified by `backend/tests/test_local_runs.py`.
   4. [verified] Screenshot de falha do hook aparece hasheado em
      `evidences/` — verified by `backend/tests/test_local_runs.py`.

Nota de implementação (não muda EARS): o comando behave roda com
`cwd=local_path` e sem path posicional — o behave resolve `./features`;
passar o repo como argumento o faria tratar a raiz como diretório de
features.
