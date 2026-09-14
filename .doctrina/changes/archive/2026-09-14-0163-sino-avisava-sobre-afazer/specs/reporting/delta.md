# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

```ops
append-requirement event: When um afazer aberto vence hoje ou ja venceu, the system shall anuncia-lo no sino, tratando o vencido como problema e o que vence hoje como atencao.
append-requirement ubiquitous: The system shall fazer o aviso de item vencido voltar a nao lido a cada dia enquanto o vencimento persistir, para que silenciar uma vez nao silencie para sempre.
append-criterion [unverified] Afazer que vence hoje e afazer vencido aparecem no sino com o prazo na frase; afazer concluido ou futuro nao aparece; o aviso de vencido volta a nao lido no dia seguinte — verified by `backend/tests/test_sino_prazos.py`.
bump-version minor
```
