# Spec Delta — capability: defects

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/defects/spec.md`

---

M1.5 fecha o critério pendente: defeito agora aparece na matriz de
rastreabilidade na linha da story. Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `partial — M1 entrega CRUD e vínculo com resultado; exibição na matriz
   é M1.5 (spec reporting)` para
   `verified — M1 (CRUD/vínculo) + M1.5 (matriz; backend/arbites/metrics.py)`.
2. Header `**Version:**` de `0.2.0` para `0.3.0`;
   `**Last updated:** 2026-07-04`.
3. Acceptance criteria:

   2. [verified] Defeito aparece na matriz de rastreabilidade da story —
      verified by `backend/tests/test_reporting_e2e.py`.

   (critério 1 permanece como está, verificado no M1.)

Sem mudança nos requisitos EARS.
