# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

M0 implementa a capability (CRUD com folder, árvore, raw, warnings de
heading, filtros). Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — bootstrap pré-código; entra no walking skeleton (M0)` para
   `verified — M0 (backend/arbites/api.py, backend/arbites/parser.py,
   frontend/src/components/TestCaseEditor.tsx)`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-03`.
3. Acceptance criteria:

   1. [verified] Criar CT pela UI grava `.md` no folder escolhido com
      frontmatter completo — verified by `backend/tests/test_testcases.py`.
   2. [verified] Editar o `.md` externamente atualiza a UI sem ação manual
      — verified by `backend/tests/test_indexing.py`.
   3. [verified] CT manual sem `## Passos` gera warning, não erro —
      verified by `backend/tests/test_testcases.py`.
   4. [verified] `GET /tree` espelha a árvore real de `testcases/` —
      verified by `backend/tests/test_testcases.py`.

Sem mudança nos requisitos EARS.
