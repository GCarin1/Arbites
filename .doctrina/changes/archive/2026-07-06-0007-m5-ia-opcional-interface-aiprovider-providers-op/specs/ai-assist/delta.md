# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Context

M5 entrega a capability ai-assist ponta a ponta: backend (providers,
schemas, geração/revisão/negativos, guard `ai_disabled`) e a aba **IA** no
frontend (config de providers com chaves no keyring, geração com preview
aceitar/rejeitar item a item, revisão e casos negativos). Isto passa a
Implementação de `planned` → `verified` e os critérios de `[unverified]` →
`[verified]`, corrigindo os caminhos de evidência para `backend/tests/…`.

## Header (MODIFIED)

- **Implementation:** verified — M5 (backend/arbites/ai.py, backend/arbites/api.py,
  frontend/src/components/AiAssist.tsx); providers OpenAI-compatível/Anthropic/
  Gemini exercitados via httpx MockTransport.

## Acceptance criteria (MODIFIED — corrige caminho e verifica)

1. [verified] Gerar CTs de uma story real com provider OpenAI-compatível e
   Anthropic, aceitando/rejeitando item a item — verified by
   `backend/tests/test_ai_generate.py`.
2. [verified] Saída fora do schema Pydantic é rejeitada com erro claro, sem
   escrita no disco — verified by `backend/tests/test_ai_generate.py`.
3. [verified] Plataforma opera integralmente com `providers: []` — verified
   by `backend/tests/test_ai_optional.py`.
