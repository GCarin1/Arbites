# Spec Delta — capability: xray-migration

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/xray-migration/spec.md`

---

M2 implementa a capability. Mudanças a aplicar no spec:

1. Header `**Implementation:**` de
   `planned — deferido ao M2 (janela de migração antes do descomissionamento do Xray)`
   para
   `verified — M2 (backend/arbites/xray_import.py,
   frontend/src/components/XrayImport.tsx); formato suportado: Jira RSS
   com custom fields do Xray, adapter isolado com fixture de contrato`.
2. Header `**Version:**` de `0.1.0` para `0.2.0`;
   `**Last updated:** 2026-07-04`.
3. Acceptance criteria — todos comprovados por teste real:

   1. [verified] Import de XML de amostra gera CTs `.md` corretos no folder
      escolhido — verified by `backend/tests/test_xray_import.py`.
   2. [verified] Reimportar o mesmo XML não duplica CTs — verified by
      `backend/tests/test_xray_import.py`.
   3. [verified] Preview lista conflitos/skips sem tocar o disco —
      verified by `backend/tests/test_xray_import.py`.

Sem mudança nos requisitos EARS.
