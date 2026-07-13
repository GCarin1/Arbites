# Spec Delta — capability: audit

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/audit/spec.md`

---

Dois fixes no check de automação quebrada:

1. Passa a usar o `ci_monitoring.name_pattern` configurado (antes chamava
   `automation_report` sem o padrão — com padrão customizado o auditor
   nunca achava automação quebrada).
2. `created_at` sem fuso horário (execution.json editado externamente —
   workspace é editável fora do Arbites, ADR 0001) não derruba mais a
   auditoria com TypeError; a idade indeterminável vira "tempo
   desconhecido" no achado.

- EARS: bullet das 4 categorias ganha a frase do padrão configurado; novo
  bullet Unwanted-behavior sobre dado sujo externo.
- Novo critério #6 — verified by `backend/tests/test_audit.py`
  (`test_audit_broken_automation_respects_custom_ci_name_pattern`,
  `test_audit_naive_created_at_does_not_crash`).

Versão `0.1.0` → `0.1.1`.
