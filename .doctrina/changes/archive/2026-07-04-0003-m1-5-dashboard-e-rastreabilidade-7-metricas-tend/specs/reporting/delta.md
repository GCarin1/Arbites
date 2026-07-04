# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

M1.5 implementa a capability (com a exceção declarada do filtro `target`
do pass rate, que depende de targets — M3). Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — deferido ao M1.5 (após M1)` para
   `verified — M1.5 (backend/arbites/metrics.py, backend/arbites/export_pdf.py,
   frontend/src/components/Dashboard.tsx); filtro target do pass rate
   entra no M3`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-04`.
3. Acceptance criteria — todos comprovados por teste real:

   1. [verified] Reporte de sprint gerado em < 1 minuto com drill-down até
      evidência — verified by `backend/tests/test_reporting_e2e.py`.
   2. [verified] Cada métrica bate com a fórmula sobre um dataset fixture
      conhecido — verified by `backend/tests/test_metrics.py`.
   3. [verified] Export Markdown da matriz é colável no Confluence sem
      perda de estrutura — verified by `backend/tests/test_export.py`.
   4. [verified] Export PDF gerado com a matriz navegada — verified by
      `backend/tests/test_export.py`.

Sem mudança nos requisitos EARS.
