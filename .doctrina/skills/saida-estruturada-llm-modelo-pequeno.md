---
name: saida-estruturada-llm-modelo-pequeno
description: Para saída JSON confiável em modelos locais ≤ 9B, envie um EXEMPLO compacto (não o JSON Schema), ligue response_format json_object com fallback, e extraia o objeto que valida no schema ignorando raciocínio vazado.
when: Ao pedir JSON/estruturado a um LLM (LM Studio/Ollama/gemma ≤ 9B) e ele entra em loop de "Schema Analysis"/"Self Correction", reconstrói $defs/properties, vaza <think>, ou abrevia com "repita para os demais".
---

# Skill — saida-estruturada-llm-modelo-pequeno

## When to use this skill

- Vai chamar um LLM para produzir JSON validado por schema (import BDD,
  geração de CTs, resumos) e o alvo é um modelo local pequeno (≤ 9B).
- Sintomas: resposta com "Final Plan", reconstrução de `$defs`/`properties`/
  `required`, blocos `<think>`, texto fora do JSON, ou expansão incompleta
  ("CT01… repita para os demais").

## Causa raiz

Enfiar `schema.model_json_schema()` no prompt dá ao modelo pequeno um
**segundo problema** (raciocinar sobre o metaformato) além da tarefa. Ele
gasta o orçamento reconstruindo o schema e vaza esse raciocínio na saída.

## Procedure (as três defesas, use as três)

1. **Prompt guiado por EXEMPLO, não por schema.** Gere um exemplo concreto e
   preenchível a partir do modelo Pydantic (um `_example_from_model` que
   percorre os campos: str→"texto"/default, list[X]→[exemplo], BaseModel→
   recursivo). Peça "responda SÓ com um objeto neste formato, um objeto por
   item, sem 'repita'/'...'". Nunca cole o JSON Schema.
2. **`response_format: {"type":"json_object"}`** nos endpoints OpenAI-compat
   (Gemini: `generationConfig.responseMimeType`). Sempre com **fallback**:
   se o servidor devolver 400, repita sem o campo (o prompt já guia o JSON).
3. **Extração tolerante a raciocínio.** Antes de parsear: remova
   `<think>…</think>` e afins; colete TODOS os objetos `{…}` balanceados
   (string-aware) preferindo cercas ```json e do fim para o início; e
   escolha o **primeiro que valida no schema** — descartando o schema
   reconstruído que o modelo emita antes dos dados.

## Anti-patterns

- Assumir que só o `response_format` resolve — modelos locais podem ignorá-lo
  ou o servidor pode não suportá-lo; sem o exemplo + extração tolerante você
  ainda quebra.
- Pegar "o primeiro `{…}`" da resposta: costuma ser o schema reconstruído.
- Pegar "o último `{…}`" cego: pode ser lixo pós-resposta. Valide no schema.

## Related material

- `backend/arbites/ai.py` — `_example_from_model`, `_json_candidates`,
  `_strip_reasoning`, `complete()`, `OpenAICompatible._raw_complete`.
- `backend/tests/test_ai_import_robustness.py`.
- Spec `ai-assist` (critério #5). Relacionada: [[default-por-tipo-de-provider]].
