# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Requirements (EARS)

### Event-driven

- When a geração da importação é cortada no meio (timeout do modelo local) e
  o objeto JSON externo fica sem fechar, the system shall recuperar os casos
  de teste que já saíram inteiros e montar um `ImportConversion` parcial —
  incluindo a `folder` lida do cabeçalho — em vez de falhar sem preview.

## Acceptance criteria

7. [verified] Resposta truncada (objeto externo não fechado, último CT pela
   metade) ainda gera preview com os CTs completos e a pasta do cabeçalho;
   o CT incompleto é descartado — verified by
   `backend/tests/test_ai_import_robustness.py`.
