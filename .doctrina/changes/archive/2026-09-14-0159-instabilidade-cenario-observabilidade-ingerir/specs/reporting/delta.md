# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

```ops
append-requirement ubiquitous: The system shall ingerir o resultado por cenario do Cucumber JSON presente no artifact da execucao de CI, ligando cada cenario ao caso de teste pela tag, porque medida agregada nao responde qual teste especifico esta instavel.
append-requirement event: When um cenario passa e falha dentro do mesmo periodo e estava estavel no periodo anterior, the system shall anuncia-lo como instabilidade NOVA, distinguindo-a de cenario que ja balancava e de cenario que falha sempre.
append-criterion [unverified] Cucumber do artifact vira resultado por cenario; cenario que passa e falha no periodo aparece como instavel; so o que estava estavel antes entra em "o que mudou"; cenario que falha sempre nao e chamado de instavel — verified by `backend/tests/test_instabilidade.py`.
bump-version minor
```
