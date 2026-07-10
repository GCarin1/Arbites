# Tasks — Change 0033-importacao-bdd-via-llm-parar-loops-de-raciocinio

- [x] `complete()`: enviar exemplo compacto (`_example_from_model`) em vez do JSON Schema.
- [x] Extração: `_strip_reasoning` + `_json_candidates` + validar-e-escolher no schema.
- [x] `response_format: json_object` (OpenAICompatible) com fallback; Gemini `responseMimeType`.
- [x] `_IMPORT_SYSTEM`: mapeamento BDD (Given/When/Then) e "gere TODOS os casos, sem 'repita/…'".
- [x] Testes de robustez (`test_ai_import_robustness.py`) + suíte AI verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-10-0033-importacao-bdd-via-llm-parar-loops-de-raciocinio/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
