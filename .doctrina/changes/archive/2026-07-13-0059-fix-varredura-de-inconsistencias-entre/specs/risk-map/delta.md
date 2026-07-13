# Spec Delta — capability: risk-map

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/risk-map/spec.md`

---

Três fixes:

1. A regex de menção a defeito usa o prefixo CONFIGURADO
   (`id_prefixes.defect`) em vez de `DF-` hardcoded — workspace com prefixo
   customizado passava a nunca correlacionar commit↔defeito.
2. O pass rate de automação usa o `ci_monitoring.name_pattern` configurado
   (mesmo padrão do endpoint `/metrics/automation`).
3. `automation_report` é computado UMA vez por requisição em `build()` e
   repassado aos scans, em vez de recomputado por repo.

- EARS Ubiquitous atualizado (prefixo configurável; report único com padrão
  configurado); Maturity/MVP reescrito sem `DF-` literal.
- Novo critério #6 — verified by `backend/tests/test_risk_map.py`
  (`test_risk_map_respects_custom_ci_name_pattern`,
  `test_risk_map_respects_custom_defect_prefix`).

Versão `0.1.0` → `0.1.1`.
