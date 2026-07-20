# Delta — ai-assist (change 0085)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall expor `POST /ai/providers/test` que executa uma
  chamada mínima ao provider (salvo ou config inline) com timeout curto e
  devolve `{ok, error}`, exposto na UI de configuração como botão "Testar"
  por provider. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Teste de provider devolve ok para provider válido e o
  erro real (401/timeout/DNS) para inválido, sem gravar nada — verified by
  `backend/tests/test_ai_providers.py`.
