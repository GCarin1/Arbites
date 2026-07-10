# Spec — ai-assist

**Capability:** ai-assist
**Status:** active
**Implementation:** verified — M5 (backend/arbites/ai.py, backend/arbites/api.py, frontend/src/components/AiAssist.tsx); providers OpenAI-compatível/Anthropic/Gemini exercitados via httpx MockTransport
**Realizes:** SC7
**Last updated:** 2026-07-10
**Version:** 0.8.0

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
- The system shall, ao pedir saída estruturada, guiar o modelo com um
  **exemplo compacto preenchível** do JSON esperado — nunca com o dump do
  JSON Schema (`$defs`/`properties`/`required`), que induz loops de
  reconstrução de schema em modelos ≤ 9B.
- The system shall solicitar `response_format: json_object` nos providers
  OpenAI-compatíveis quando espera JSON (Gemini: `responseMimeType`), com
  **fallback** transparente (repetir sem o campo) quando o endpoint não o
  suporta.
- The system shall, ao interpretar a saída, **descartar raciocínio vazado**
  (`<think>…</think>` e afins) e escolher, dentre os objetos JSON
  candidatos, o primeiro que **valida no schema** — ignorando planos/
  reconstruções de schema emitidos antes dos dados.

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
- When um provider local de raciocínio devolve `content` vazio mas preenche
  `reasoning_content` (ex.: glm-4.7-flash via LM Studio), the system shall
  usar `reasoning_content` como fonte de JSON de fallback antes de falhar.
- When a resposta de conversão de import vem truncada (geração cortada por
  timeout do modelo local — objeto JSON externo não fecha), the system shall
  recuperar os casos de teste que saíram inteiros e apresentá-los como
  preview parcial (com a pasta lida do cabeçalho), em vez de falhar sem
  preview.
- When o arquivo enviado para importação já está em Gherkin/BDD (contém
  Scenario + passos Given/When/Then), the system shall separá-lo por um parser
  determinístico e preservar o texto VERBATIM (Feature, título e cada passo,
  inclusive múltiplos And), sem IA e sem exigir provider configurado — não
  deve parafrasear, trocar a Feature pelo título, adicionar pontuação nem
  fundir passos.

### State-driven

- While nenhum provider está configurado (`default_provider: null`), the
  system shall ocultar/desabilitar as funções de IA mantendo todo o resto
  da plataforma funcional.
- While a IA processa uma importação, the system shall submeter a conversão
  apenas por ação explícita do usuário (botão "Enviar"), nunca no simples
  `onChange` de seleção de arquivo, e sinalizar que modelos locais de
  raciocínio podem levar minutos (timeout do cliente HTTP ≥ 300 s).

### Unwanted-behavior (must-not)

- The system shall not gravar qualquer saída de IA no disco sem
  confirmação explícita do usuário na UI.
- The system shall not armazenar chaves de API fora do keyring.
- The system shall not incluir JSON Schema no prompt de saída estruturada,
  nem falhar a conversão por raciocínio vazado ou por um objeto JSON extra
  (schema reconstruído) preceder os dados válidos.
- The system shall not anexar linhas não reconhecidas (cabeçalhos markdown
  como `### CTxx - ...`, comentários, numeração, prosa entre cenários) ao
  último passo de um cenário Gherkin durante o parse verbatim; apenas passos
  Given/When/Then/And/But e linhas de tabela de dados (`| a | b |`) são
  anexados.

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

5. [verified] Resposta com `<think>`, "Final Plan" e um objeto de schema
   reconstruído antes dos dados ainda produz o `ImportConversion` correto; o
   prompt leva exemplo compacto (não JSON Schema); `response_format:
   json_object` é enviado, com fallback quando o servidor o rejeita (400) —
   verified by `backend/tests/test_ai_import_robustness.py`.

6. [verified] Resposta com `content` vazio e o JSON dentro de
   `reasoning_content` (modelo de raciocínio) ainda produz o
   `ImportConversion` correto — verified by
   `backend/tests/test_ai_import_robustness.py`.

7. [verified] Saída de import truncada no meio de um caso produz um
   `ImportConversion` com os casos completos anteriores e a pasta recuperada
   do cabeçalho; o caso incompleto é descartado — verified by
   `backend/tests/test_ai_import_robustness.py`.

8. [verified] Importar um .txt já em Gherkin devolve o corpo idêntico ao
   enviado (Feature preservada, "que" e ambos os And intactos), com a pasta =
   slug da Feature, sem tocar no provider de IA — verified by
   `backend/tests/test_ai_import.py`.

9. [verified] Um `### CTxx - ...` (cabeçalho markdown usado como separador
   entre cenários no arquivo de origem) não aparece no corpo do cenário
   anterior nem quebra a separação em dois cenários — verified by
   `backend/tests/test_ai_import.py`.

## Maturity

**MVP (committed):**

- 4 classes de provider, 3 funções (gerar/revisar/negativos), preview
  obrigatório, config UI.

**Future (aspirational, not committed):**

- Sugestão automática de tags; geração de dados de teste.

## Out of scope for this spec

- Qualquer função central da plataforma depender de IA (princípio 4).
