# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall enriquecer `GET /metrics/automation` com: os CTs que mais
  falham nos runs de automação (`top_failing_testcases`, pior-primeiro); por
  repositório, o histórico recente de desfechos (`recent`, para sparkline), o
  MTTR em horas (tempo médio até voltar ao verde) e `broken_since` quando o
  repo segue vermelho, e a contagem de CTs flaky (`flaky`); e a lista global
  de CTs flaky em automação (`flaky_testcases`).
- The system shall aceitar o filtro opcional `env` em `GET /metrics/automation`
  (ambiente extraído do nome), mantendo `envs` com todos os ambientes
  disponíveis para o seletor mesmo quando filtrado.

## Acceptance criteria

9. [verified] `GET /metrics/automation` expõe ranking de CTs que mais falham,
   sparkline/MTTR/`broken_since`/flaky por repo, lista global de flaky, e o
   filtro `env` (com `envs` completo) — verified by
   `backend/tests/test_automation_report.py`.
