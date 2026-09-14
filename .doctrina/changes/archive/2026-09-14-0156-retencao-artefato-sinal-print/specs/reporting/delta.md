# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

```ops
append-requirement ubiquitous: The system shall aplicar retencao independente a sinal e a anexo de execucao de CI, guardando o sinal por muito mais tempo que o anexo, para que a serie temporal continue respondendo depois que a captura daquele dia ja foi descartada.
append-requirement ubiquitous: The system shall exibir o espaco ocupado e uma previa do que a proxima limpeza removeria antes de remover, e mover o removido para a lixeira em vez de apagar direto.
append-criterion [unverified] Anexo expirado e removido para a lixeira e a serie temporal do mesmo periodo continua respondendo; a previa da limpeza corresponde ao que e removido — verified by `backend/tests/test_retencao_ci.py`.
bump-version minor
```
