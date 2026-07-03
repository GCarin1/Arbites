# Spec Delta — capability: indexing

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/indexing/spec.md`

---

M0 implementa parsers (frontmatter + headings), reindex completo e
incremental, warnings e contadores. O scan de Gherkin/features fica para o
M3 (targets ainda não existem). Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — bootstrap pré-código; entra no walking skeleton (M0)` para
   `partial — M0 entrega parsers/reindex/warnings; scan Gherkin de targets
   fica para o M3 (spec local-automation)`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-03`.
3. Acceptance criteria:

   1. [verified] Editar um CT em editor externo reflete na API/UI em
      segundos sem ação manual — verified by
      `backend/tests/test_indexing.py`.
   2. [verified] Reindex de workspace com 2.000 CTs conclui em < 5 s —
      verified by `backend/tests/test_indexing_perf.py`.
   3. [verified] ID duplicado gera conflito listado em `/warnings` —
      verified by `backend/tests/test_indexing.py`.
   4. [unverified] Feature em `# language: pt` é parseada e mapeada por
      tag `@CT-XXXX` — deferido ao M3; verified by
      `backend/tests/test_gherkin.py` (a criar).

Sem mudança nos requisitos EARS.
