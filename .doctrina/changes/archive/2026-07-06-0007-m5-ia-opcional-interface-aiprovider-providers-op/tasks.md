# Tasks — Change 0007-m5-ia-opcional-interface-aiprovider-providers-op

- [x] Backend: `ai.py` — AIKeyStore (keyring), OpenAICompatible /
      Anthropic / Gemini, complete() com validação Pydantic e extração de
      JSON.
- [x] Backend: funções de geração (schema GeneratedTestcases), revisão
      (com candidatos de duplicidade do índice) e casos negativos.
- [x] Backend: rotas `GET/PUT /ai/providers`, `POST /ai/generate-testcases`,
      `POST /ai/review/{id}`, `POST /ai/negative-cases/{id}` + guard
      `ai_disabled` (409) sem provider default.
- [x] Backend: `test_ai_generate.py` (MockTransport OpenAI-compatível e
      Anthropic, aceite item a item via POST /testcases, schema inválido
      rejeitado sem escrita) e `test_ai_optional.py` (providers: []).
- [x] Frontend: aba IA — config/chaves, geração com preview
      aceitar/rejeitar, revisão e negativos (`frontend/src/components/AiAssist.tsx`).
- [x] Delta: ai-assist → verified (caminhos de evidência corrigidos p/ `backend/tests/…`).
- [x] `doctrina analyze` limpo e `doctrina verify` verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-04-0007-m5-ia-opcional-interface-aiprovider-providers-op/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
