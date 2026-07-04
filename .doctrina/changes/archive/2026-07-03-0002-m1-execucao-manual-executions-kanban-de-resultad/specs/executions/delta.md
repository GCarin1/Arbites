# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

M1 implementa a capability por completo (ciclo manual). Mudanças a aplicar
no spec:

1. Header `**Implementation:**` de
   `planned — deferido ao M1 (após o walking skeleton M0)` para
   `verified — M1 (backend/arbites/executions.py, backend/arbites/api.py,
   frontend/src/components/Executions.tsx)`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-03`.
3. Acceptance criteria — todos comprovados por teste real:

   1. [verified] Regressão manual de ~20 CTs com evidências e defeito
      vinculado completa sem sair da plataforma — verified by
      `backend/tests/test_executions_e2e.py`.
   2. [verified] Drag no Kanban persiste no `execution.json` e gera evento
      de history — verified by `backend/tests/test_executions.py`.
   3. [verified] Upload de evidência grava arquivo + SHA-256 corretos —
      verified by `backend/tests/test_executions.py`.
   4. [verified] Mesmo CT com resultados distintos em duas executions não
      gera conflito — verified by `backend/tests/test_executions.py`.

Sem mudança nos requisitos EARS (o comportamento implementado é o
especificado, incluindo snapshot de steps na criação — decisão de design
do change registrada em design.md).
