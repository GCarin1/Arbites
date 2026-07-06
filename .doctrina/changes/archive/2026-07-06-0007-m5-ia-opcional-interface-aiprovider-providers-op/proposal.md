# Change 0007-m5-ia-opcional-interface-aiprovider-providers-op — M5 - IA opcional: interface AIProvider, providers OpenAI/Anthropic/Gemini/OpenAI-compativel, geracao de CTs a partir de story, revisao, casos negativos, tudo com preview e chaves no keyring

- **Status:** proposed
- **Date:** 2026-07-04
- **Owner:** Gcarini
- **Affects specs:** ai-assist

## Why

M5 é o último milestone da v1 (SC7): gerar CTs a partir de uma story real
(critérios EARS como insumo), revisar CTs e propor casos negativos —
estritamente opcional (princípio 4: a plataforma é 100% funcional sem
nenhum provider) e sempre com preview (nada é gravado sem confirmação
explícita).

## What

- `backend/arbites/ai.py` — interface `AIProvider.complete(system, user,
  schema)`; 3 classes cobrem os 7 providers do intake:
  `OpenAICompatible` (OpenAI, OpenRouter, Ollama, LM Studio, vLLM — só
  muda a base URL), `AnthropicProvider`, `GeminiProvider`. Saída com
  schema é validada por Pydantic; fora do schema → erro claro, sem
  escrita. Chaves no keyring (service `arbites-ai`), nunca em YAML.
- Funções: geração de CTs a partir de story (preview aceitável item a
  item — o aceite é o próprio `POST /testcases` existente), revisão
  (passos ambíguos, duplicidade contra o índice por título/tags,
  resultado esperado vago) e casos negativos.
- API M5: `GET/PUT /ai/providers` (config no arbites.yaml + status das
  chaves; a chave entra pelo PUT e vai direto ao keyring),
  `POST /ai/generate-testcases`, `POST /ai/review/{testcase_id}`,
  `POST /ai/negative-cases/{testcase_id}`. Sem provider default → 409
  `ai_disabled` e o resto da plataforma intacto.
- Providers recebem transporte httpx injetável: os testes usam
  `httpx.MockTransport` simulando um endpoint OpenAI-compatível (o caso
  LM Studio) e o shape da Anthropic (caso cloud) — sem rede no gate.
- Frontend: aba IA — config de providers/chaves, geração com preview
  aceitar/rejeitar por item, revisão e negativos a partir de um CT.
- Testes: `backend/tests/test_ai_generate.py`, `test_ai_optional.py`.

## Scope boundaries

- Chamadas a LLMs reais ficam fora do gate (rede/chave); o contrato dos
  shapes OpenAI/Anthropic/Gemini fica fixado nos mocks.
- Sugestão de tags e geração de dados de teste: Future da spec.

## Verification

- [x] `doctrina verify` verde — pytest (inclui `test_ai_generate.py` + `test_ai_optional.py`, 8 casos) e build do frontend (tsc + vite), com a aba IA.
- [x] Critérios de aceite da ai-assist verificados com evidência em `backend/tests/…` (`doctrina coverage` — corrigido o caminho antigo `tests/…`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
