# Change 0033-importacao-bdd-via-llm-parar-loops-de-raciocinio — importacao BDD via LLM: parar loops de raciocinio/reconstrucao de schema em modelos locais pequenos; enviar exemplo compacto em vez de JSON Schema; usar response_format json_object; extrair JSON ignorando raciocinio e escolhendo o objeto que valida no schema

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** ai-assist

## Why

importacao BDD via LLM: parar loops de raciocinio/reconstrucao de schema em modelos locais pequenos; enviar exemplo compacto em vez de JSON Schema; usar response_format json_object; extrair JSON ignorando raciocinio e escolhendo o objeto que valida no schema

## What

- **backend/arbites/ai.py** — em `complete()`, prompt de saída estruturada passa
  a levar um **exemplo compacto** (`_example_from_model`) em vez do JSON Schema.
- Extração robusta: `_strip_reasoning` remove `<think>…</think>`; `_json_candidates`
  reúne objetos JSON (cercas ```json e do fim para o início) e `complete()` retorna
  o **primeiro que valida no schema** — descarta raciocínio/reconstrução de schema.
- `response_format: json_object` nos providers OpenAI-compatíveis com fallback;
  Gemini usa `responseMimeType: application/json`.
- `_IMPORT_SYSTEM`: mapeamento BDD Given/When/Then e "gere TODOS os casos".
- **ai-assist spec** MODIFIED (delta) + critério [verified] #5.

## Scope boundaries

- Não muda a UI de importação nem o schema `ImportConversion`; só o contrato
  prompt↔saída e a leitura da resposta. Demais funções de IA herdam a mesma
  robustez por usarem `complete()`.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `python -m pytest backend/tests` verde (113) — inclui `test_ai_import_robustness.py`.
- [x] Critério #5 do ai-assist cita `backend/tests/test_ai_import_robustness.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
