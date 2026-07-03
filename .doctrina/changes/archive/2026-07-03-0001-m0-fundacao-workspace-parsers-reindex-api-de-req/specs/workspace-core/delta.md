# Spec Delta — capability: workspace-core

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/workspace-core/spec.md`

---

M0 implementa a capability. Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — bootstrap pré-código; entra no walking skeleton (M0)` para
   `verified — M0 (backend/arbites/workspace.py, backend/arbites/api.py)`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-03`.
3. Acceptance criteria — todos comprovados por teste real:

   1. [verified] `GET /workspace` retorna a config do `arbites.yaml` e o
      status do índice — verified by `backend/tests/test_workspace.py`.
   2. [verified] Apagar `index.db` e reindexar reconstrói o índice sem
      perda de dados — verified by `backend/tests/test_workspace.py`.
   3. [verified] Criar um CT via API consome o contador e grava `.md` com
      ID no frontmatter — verified by `backend/tests/test_workspace.py`.
   4. [verified] DELETE move o arquivo para `.arbites/trash/` e ele é
      removido do índice — verified by `backend/tests/test_workspace.py`.

Sem mudança nos requisitos EARS (o comportamento implementado é o
especificado).
