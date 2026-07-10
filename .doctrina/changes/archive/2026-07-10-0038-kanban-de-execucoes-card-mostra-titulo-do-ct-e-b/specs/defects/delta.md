# Spec Delta — capability: defects

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/defects/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall expor `POST /executions/{exec_id}/results/{ct_id}/defects`
  (vincular um defeito já existente, por id) e
  `DELETE /executions/{exec_id}/results/{ct_id}/defects/{defect_id}`
  (desvincular), além do vínculo automático ao criar defeito a partir de um
  resultado `failed`.

### Unwanted-behavior (must-not)

- The system shall not aceitar vincular um `defect_id` inexistente (404) nem
  vincular/desvincular numa execution `closed` (409).

## Acceptance criteria

4. [verified] Vincular um defeito pré-existente a um resultado, vincular de
   novo (idempotente, sem duplicar) e desvincular funcionam via API dedicada;
   `defect_id` inexistente e execution fechada são rejeitados — verified by
   `backend/tests/test_executions.py`.
