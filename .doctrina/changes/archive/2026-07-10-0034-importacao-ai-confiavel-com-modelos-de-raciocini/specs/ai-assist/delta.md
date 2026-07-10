# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Requirements (EARS)

### Event-driven

- When um provider local de raciocínio devolve `content` vazio mas preenche
  `reasoning_content` (ex.: glm-4.7-flash via LM Studio), the system shall
  usar `reasoning_content` como fonte de JSON de fallback antes de falhar.

### State-driven

- While a IA processa uma importação, the system shall submeter a conversão
  apenas por ação explícita do usuário (botão "Enviar"), nunca no simples
  `onChange` de seleção de arquivo, e sinalizar que modelos locais de
  raciocínio podem levar minutos (timeout do cliente HTTP ≥ 300 s).

## Acceptance criteria

6. [verified] Resposta com `content` vazio e o JSON dentro de
   `reasoning_content` ainda produz o `ImportConversion` correto — verified by
   `backend/tests/test_ai_import_robustness.py`.
