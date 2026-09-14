# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

```ops
append-requirement ubiquitous: The system shall ingerir execucoes de CI que nao foram disparadas por ele, descobrindo-as por consulta periodica ao provedor, com idempotencia por identificador de run.
append-requirement event: When a ingestao volta depois de um periodo parada, the system shall recuperar o intervalo inteiro que passou, e nao apenas a execucao mais recente.
append-criterion [unverified] Run criado por agendamento no provedor aparece sem disparo local, ingerir duas vezes nao duplica, e retomar apos parada traz o intervalo completo — verified by `backend/tests/test_ci_ingest.py`.
bump-version minor
```
