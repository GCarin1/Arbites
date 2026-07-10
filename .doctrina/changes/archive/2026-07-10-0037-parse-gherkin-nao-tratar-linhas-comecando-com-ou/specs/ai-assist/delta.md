# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Requirements (EARS)

### Unwanted-behavior (must-not)

- The system shall not anexar linhas não reconhecidas (cabeçalhos markdown
  como `### CTxx - ...`, comentários, numeração, prosa entre cenários) ao
  último passo de um cenário Gherkin durante o parse verbatim; apenas passos
  Given/When/Then/And/But e linhas de tabela de dados (`| a | b |`) são
  anexados.

## Acceptance criteria

9. [verified] Um `### CTxx - ...` (cabeçalho markdown usado como separador
   entre cenários no arquivo de origem) não aparece no corpo do cenário
   anterior nem quebra a separação em dois cenários — verified by
   `backend/tests/test_ai_import.py`.
