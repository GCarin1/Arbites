# Change 0085-testar-provider-de-ia-na-configuracao — testar provider de IA na configuracao

- **Status:** applied
- **Applied:** 2026-07-20
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** ai-assist

## Why

Na config de providers não há "testar": você salva e só descobre chave
errada/URL fora do ar quando a geração falha, com erro fora de contexto.

## What

- Backend: `POST /ai/providers/test` (body: name, ou config inline ainda
  não salva) → chamada mínima ao provider com timeout curto → `{ok, error}`.
- UI: botão "Testar" por linha da tabela de providers e no form de novo
  provider; dot ok/erro + mensagem do erro real (timeout, 401, DNS).

## Scope boundaries

- Teste é chamada mínima (1 completion curta) — sem validar modelo/custo.
- Não bloqueia salvar (aviso, não gate).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Provider válido → ok; chave inválida/URL fora → erro com mensagem; provider inline (não salvo) testável — `backend/tests/test_ai_providers.py` (MockTransport).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
