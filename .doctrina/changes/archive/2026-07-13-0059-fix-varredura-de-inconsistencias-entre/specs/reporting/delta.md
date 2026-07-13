# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

Fix: o componente de automação do Health Score passa a usar o
`ci_monitoring.name_pattern` configurado (mesmo padrão do endpoint
`/metrics/automation`). Antes, `health_score` chamava `automation_report`
sem o padrão — com padrão customizado, todos os runs viravam `unparsed` e o
componente ficava `None` silenciosamente.

- EARS Ubiquitous do Health Score ganha a frase sobre o padrão configurado.
- Critério #12 estendido para cobrir o padrão customizado — verified by
  `backend/tests/test_health_score.py`
  (`test_health_score_respects_custom_ci_name_pattern`).

Versão `0.10.0` → `0.10.1`.
