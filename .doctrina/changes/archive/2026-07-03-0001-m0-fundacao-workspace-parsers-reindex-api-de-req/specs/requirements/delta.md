# Spec Delta — capability: requirements

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/requirements/spec.md`

---

M0 implementa a capability (CRUD epic/story, filtros, warning de epic
inexistente, trash). Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — bootstrap pré-código; entra no walking skeleton (M0)` para
   `verified — M0 (backend/arbites/api.py, backend/arbites/indexer.py)`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-03`.
3. Acceptance criteria:

   1. [verified] Criar epic e story pela API gera `.md` válidos em
      `requirements/` com IDs sequenciais — verified by
      `backend/tests/test_requirements.py`.
   2. [verified] `GET /requirements?kind=story&status=active` filtra
      corretamente — verified by `backend/tests/test_requirements.py`.
   3. [verified] Story com `epic` inexistente aparece em `/warnings` —
      verified by `backend/tests/test_requirements.py`.

Sem mudança nos requisitos EARS.
