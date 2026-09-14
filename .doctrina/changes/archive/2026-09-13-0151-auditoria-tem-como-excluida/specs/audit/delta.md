# Spec Delta — capability: audit

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/audit/spec.md`

---

```ops
append-requirement ubiquitous: The system shall permitir que uma conta administradora exclua uma rodada de auditoria, individualmente ou em lote por data anterior, movendo o documento para a lixeira como qualquer outro artefato do workspace, em vez de apagar direto.
append-requirement unwanted: The system shall not permitir que papel diferente de administrador exclua rodada de auditoria, nem expor qualquer rota que remova o log de atividade, que e continuo e imutavel.
append-criterion [unverified] Admin exclui rodada individual e em lote por data, o documento vai para a lixeira e pode ser restaurado, o lote nao leva rodada posterior a data, e viewer e editor recebem 403 nas duas — verified by `backend/tests/test_audit.py`.
bump-version minor
```
