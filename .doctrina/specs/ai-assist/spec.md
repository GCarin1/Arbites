# Spec — ai-assist

**Capability:** ai-assist
**Status:** active
**Implementation:** verified — M5 (backend/arbites/ai.py, backend/arbites/api.py, frontend/src/components/AiAssist.tsx); providers OpenAI-compatível/Anthropic/Gemini exercitados via httpx MockTransport
**Realizes:** SC7
**Last updated:** 2026-07-09
**Version:** 0.3.0

## Purpose

Funções de IA estritamente opcionais: gerar CTs a partir de stories (com
critérios EARS como insumo), revisar CTs e propor casos negativos. Uma
interface única `AIProvider` cobre OpenAI, Anthropic, Gemini e todos os
OpenAI-compatíveis (OpenRouter, Ollama, LM Studio, vLLM) em ~4 classes.
Toda saída é preview: nada é gravado sem confirmação explícita.

## Requirements (EARS)

### Ubiquitous

- The system shall definir a interface
  `AIProvider.complete(system, user, schema) -> str | BaseModel`.
- The system shall implementar os providers OpenAI, Anthropic, Gemini e
  `OpenAICompatible` (base URL configurável cobrindo OpenRouter, Ollama,
  LM Studio, vLLM).
- The system shall configurar providers no `arbites.yaml` e chaves no
  keyring do SO.
- The system shall expor `GET/PUT /ai/providers`,
  `POST /ai/generate-testcases`, `POST /ai/review/{testcase_id}`,
  `POST /ai/negative-cases/{testcase_id}`.
- The system shall validar a saída de geração de CTs contra schema
  Pydantic antes de apresentar o preview.

- The system shall expor `POST /import/ai` (upload .txt/.md/.xml) que usa a
  IA para identificar casos de teste em texto livre, sugerir uma pasta e
  convertê-los para BDD — sempre preview; o aceite é o `POST /testcases`
  normal. Prompt enxuto (modelos ≤ 9B).

### Event-driven

- When o usuário solicita geração a partir de uma story, the system shall
  produzir uma lista de CTs como diff/preview aceitável/rejeitável item a
  item.
- When o usuário solicita revisão de um CT, the system shall apontar
  passos ambíguos, duplicidade contra o índice (busca por título/tags
  similares) e resultado esperado vago.
- When o usuário solicita casos negativos, the system shall propor
  variações do CT positivo (campos vazios, caracteres especiais, limites).

### State-driven

- While nenhum provider está configurado (`default_provider: null`), the
  system shall ocultar/desabilitar as funções de IA mantendo todo o resto
  da plataforma funcional.

### Unwanted-behavior (must-not)

- The system shall not gravar qualquer saída de IA no disco sem
  confirmação explícita do usuário na UI.
- The system shall not armazenar chaves de API fora do keyring.

### Optional

- Where um endpoint OpenAI-compatível local está configurado (LM Studio),
  the system may operar 100% offline para as funções de IA.

## Acceptance criteria

1. [verified] Gerar CTs de uma story real com provider OpenAI-compatível e
   Anthropic, aceitando/rejeitando item a item — verified by
   `backend/tests/test_ai_generate.py`.
2. [verified] Saída fora do schema Pydantic é rejeitada com erro claro,
   sem escrita no disco — verified by `backend/tests/test_ai_generate.py`.
3. [verified] Plataforma opera integralmente com `providers: []` —
   verified by `backend/tests/test_ai_optional.py`.

4. [verified] Arquivo livre vira preview BDD (pasta sugerida + Given/When/
   Then), nada gravado sem aceite; extensão inválida/arquivo vazio → 422 —
   verified by `backend/tests/test_ai_import.py`.

## Maturity

**MVP (committed):**

- 4 classes de provider, 3 funções (gerar/revisar/negativos), preview
  obrigatório, config UI.

**Future (aspirational, not committed):**

- Sugestão automática de tags; geração de dados de teste.

## Out of scope for this spec

- Qualquer função central da plataforma depender de IA (princípio 4).
