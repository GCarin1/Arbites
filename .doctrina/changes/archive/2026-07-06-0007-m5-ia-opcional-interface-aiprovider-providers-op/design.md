# Design — Change 0007-m5-ia-opcional-interface-aiprovider-providers-op

## Approach

Uma interface, três classes: `OpenAICompatible` cobre OpenAI, OpenRouter,
Ollama, LM Studio e vLLM (o que muda é `base_url` e `model` — exatamente a
redução prevista no intake §12), mais `AnthropicProvider` e
`GeminiProvider`. `complete(system, user, schema)` com schema anexa a
instrução de responder JSON puro, extrai o primeiro bloco JSON da resposta
e valida com Pydantic — validação falhou é `AIProviderError` com a
mensagem do validador, e nada chega ao disco (as rotas de IA nunca
escrevem; o aceite de um item do preview é o `POST /testcases` normal, que
o usuário dispara na UI).

Config vive em `arbites.yaml → ai:` (nomes, kind, model, base_url);
chaves só no keyring (`arbites-ai`/<provider>), entrando pelo
`PUT /ai/providers` e saindo apenas como `{configured: bool}`. Os
providers recebem `httpx.BaseTransport` injetável via
`create_app(ai_transport=...)`: os testes simulam um endpoint
OpenAI-compatível (LM Studio) e o shape da Anthropic com `MockTransport`.

A duplicidade na revisão é híbrida: o backend consulta o índice por
título/tags similares e entrega os candidatos ao modelo no prompt — o
LLM aponta, o índice fundamenta.

## Alternatives considered

- SDKs oficiais (openai, anthropic, google-genai) — rejeitado: três SDKs
  pesados para três POSTs; httpx cru mantém os shapes explícitos e
  testáveis.
- Endpoint de "confirm" próprio da IA — rejeitado: o aceite é o
  `POST /testcases` que já existe; menos superfície, mesma garantia de
  preview obrigatório.

## Trade-offs and risks

- Shapes das APIs fixados à mão podem defasar — mitigado por serem 3
  endpoints estáveis e públicos; mocks documentam o contrato esperado.
- Extração de JSON de respostas com texto ao redor usa heurística de
  primeiro bloco `{...}` — falha vira erro claro, nunca escrita suja.

## Decisions to record as ADRs

Nenhuma nova — executa o princípio 4 do intake e o padrão de segredo do
ADR 0008.
