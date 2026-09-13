# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

```ops
append-requirement unwanted: The system shall not gravar resultado para um cenario que foi interrompido antes de terminar — ausencia de falha observada num cenario morto por timeout ou cancelamento nao e aprovacao, e o caso segue pendente ate ser marcado blocked.
append-criterion [unverified] Um cenario morto no meio por timeout nunca chega a execution como `passed`; chega `blocked` com `error: "timeout"` — verified by `backend/tests/test_local_runs.py`.
bump-version minor
```
