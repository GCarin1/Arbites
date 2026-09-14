# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

```ops
append-requirement state: While a instancia nao tem cofre de credenciais do sistema operacional, the system shall responder que nao ha credencial em vez de falhar, mantendo a aplicacao inteira utilizavel.
append-requirement ubiquitous: The system shall aceitar a credencial de CI pela variavel de ambiente do processo onde o cofre do sistema operacional nao existe, com precedencia sobre o cofre, sem nunca devolver o valor nem grava-lo no workspace.
append-requirement event: When alguem tenta guardar a credencial numa instancia sem cofre, the system shall recusar explicando a saida, em vez de aceitar em silencio ou falhar depois.
append-criterion [unverified] Instancia sem cofre responde a tela de problemas e o status do token sem erro, anuncia a falta com o remedio, recusa a gravacao explicando, e aceita a credencial pelo ambiente sem vazar o valor nem toca-lo no disco — verified by `backend/tests/test_sem_cofre.py`.
bump-version minor
```
