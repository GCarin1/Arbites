# Spec Delta — capability: defects

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/defects/spec.md`

---

M1 implementa o defeito mínimo (CRUD + vínculo com resultado). A exibição
na matriz de rastreabilidade é M1.5 (spec reporting). Mudanças a aplicar
no spec:

1. Header `**Implementation:**` de
   `planned — deferido ao M1 (após o walking skeleton M0)` para
   `partial — M1 entrega CRUD e vínculo com resultado; exibição na matriz
   é M1.5 (spec reporting)`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-03`.
3. Acceptance criteria:

   1. [verified] Criar defeito a partir de um resultado failed vincula
      `testcase` e `execution` — verified by `backend/tests/test_defects.py`.
   2. [unverified] Defeito aparece na matriz de rastreabilidade da story —
      deferido ao M1.5; verified by `backend/tests/test_reporting_e2e.py`
      (a criar).

Sem mudança nos requisitos EARS.
