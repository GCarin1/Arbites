# Delta — local-automation (change 0090)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- When o usuário aplica "update" (re-base de steps) na sync de features,
  the system shall marcar o CT com `needs_rerun: true`; when um novo
  resultado do CT é registrado em execution posterior, the system shall
  limpar o flag automaticamente. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Apply de update marca o CT e um resultado posterior
  limpa o flag — verified by `backend/tests/test_feature_sync.py`.
