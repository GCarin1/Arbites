# Spec Delta — capability: indexing

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/indexing/spec.md`

---

M3 fecha a lacuna do M0: scan de features Gherkin dos targets (pacote
oficial `gherkin`, `# language: pt`, mapa `@CT-XXXX`, warnings de
integridade), integrado ao reindex completo e ao scan manual. Mudanças a
aplicar no spec:

1. Header `**Implementation:**` de
   `partial — M0 entrega parsers/reindex/warnings; scan Gherkin de targets
   fica para o M3 (spec local-automation)` para
   `verified — M0 (parsers/reindex) + M3 (scan Gherkin:
   backend/arbites/gherkin_scan.py)`.
2. Header `**Version:**` de `0.2.0` para `0.3.0`;
   `**Last updated:** 2026-07-04`.
3. Acceptance criterion 4:

   4. [verified] Feature em `# language: pt` é parseada e mapeada por tag
      `@CT-XXXX` — verified by `backend/tests/test_gherkin.py`.

Sem mudança nos requisitos EARS.
