# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

M2 adiciona `external_key` ao frontmatter do CT (chave do sistema de
origem, usada pela idempotência da migração Xray e futuramente pelo
Businessmap). Mudanças a aplicar no spec:

1. Em `## Requirements (EARS)` → `### Ubiquitous`, acrescentar:

   - The system shall aceitar `external_key` opcional no frontmatter do
     CT (chave no sistema externo de origem) e indexá-la para detecção de
     duplicidade na migração (spec `xray-migration`).

2. Header `**Version:**` de `0.2.0` para `0.3.0`;
   `**Last updated:** 2026-07-04`. Implementation permanece `verified`
   (comportamento coberto por `backend/tests/test_xray_import.py`).

Critérios de aceite inalterados.
