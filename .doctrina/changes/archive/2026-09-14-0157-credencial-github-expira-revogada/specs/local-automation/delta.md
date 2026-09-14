# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

```ops
append-requirement state: While a credencial do provedor de CI esta perto de expirar ou foi recusada, the system shall registrar um problema visivel com o motivo, em vez de deixar a ingestao parar em silencio.
append-requirement ubiquitous: The system shall distinguir ingestao parada por credencial de ausencia de execucao nova, porque os dois estados parecem iguais e pedem acoes opostas.
append-criterion [unverified] Credencial perto de expirar aparece em Problemas antes de expirar, recusa do provedor vira problema com motivo, e repor a credencial retoma a ingestao sem perder o intervalo — verified by `backend/tests/test_credencial_ci.py`.
bump-version minor
```
