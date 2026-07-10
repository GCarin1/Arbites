# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall, ao pedir saída estruturada (schema Pydantic), guiar o
  modelo com um **exemplo compacto preenchível** do JSON esperado — nunca
  com o dump do JSON Schema (`$defs`/`properties`/`required`), que induz
  loops de reconstrução de schema em modelos ≤ 9B.
- The system shall solicitar `response_format: json_object` nos providers
  OpenAI-compatíveis quando espera JSON, com **fallback** transparente
  (repetir sem `response_format`) quando o endpoint não o suporta.
- The system shall, ao interpretar a saída, **descartar raciocínio vazado**
  (`<think>…</think>` e afins) e escolher, dentre os objetos JSON candidatos,
  o primeiro que **valida no schema** — ignorando planos/reconstruções de
  schema que o modelo emita antes dos dados.

### Unwanted-behavior (must-not)

- The system shall not incluir JSON Schema no prompt de saída estruturada.
- The system shall not falhar a importação por texto de raciocínio ou por um
  objeto JSON extra (ex.: schema reconstruído) preceder os dados válidos.

## Acceptance criteria

5. [verified] Resposta com `<think>`, "Final Plan" e um objeto de schema
   reconstruído antes dos dados ainda produz o `ImportConversion` correto;
   `response_format: json_object` é enviado e há fallback quando o servidor
   o rejeita (400) — verified by
   `backend/tests/test_ai_import_robustness.py`.
