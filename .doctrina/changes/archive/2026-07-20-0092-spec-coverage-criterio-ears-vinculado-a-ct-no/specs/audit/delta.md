# Delta — audit (change 0092)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall consolidar a categoria `spec` na auditoria: critério
  EARS sem CT vinculado (warn) e CT ready/automated de story com critérios
  sem vínculo `criteria` (info) — mesmo padrão de severidade/ref das demais
  categorias. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Rodada de auditoria acusa critérios descobertos e CTs
  sem vínculo — verified by `backend/tests/test_audit.py`.
