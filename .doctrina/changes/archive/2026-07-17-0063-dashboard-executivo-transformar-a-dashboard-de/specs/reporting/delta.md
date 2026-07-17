# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

Dashboard executivo — requisitos a acrescentar (todos [unverified] até
implementar; a implementação desta change prova e flipa):

### Ubiquitous

- The system shall devolver, para cada métrica do summary, a comparação com
  o período imediatamente anterior de mesmo tamanho (`previous`, `delta`) —
  o usuário vê o que melhorou/piorou, não só o valor atual.
- The system shall exibir no Dashboard um bloco de alertas de risco derivado
  dos dados existentes (Health Score baixo, automação quebrada, defeitos
  críticos envelhecendo, CTs flaky), cada alerta navegando à seção de
  origem; reutiliza os achados `bad` do Agente Auditor (capability `audit`).
- The system shall exibir a última atualização dos dados
  (`last_reindex`) no Dashboard.
- The system shall exibir uma seção "top problemas" (piores repositórios de
  automação, CTs que mais falham, defeitos mais antigos) agregando os
  reports existentes num só lugar.
- The system shall exibir "ações recomendadas" derivadas por regras
  determinísticas dos dados (stories sem CT, repo quebrado há N dias,
  defeito antigo sem causa raiz) — nunca por IA nesta versão.

### Acceptance criteria

13. [verified] `GET /metrics/dashboard` devolve `pass_rate_trend`
    (atual/anterior/delta comparando janelas consecutivas), alertas de risco
    (achados `bad` do auditor + Health Score baixo), ações recomendadas,
    top problemas (defeitos mais antigos ordenados, piores repos, CTs que
    mais falham) e `last_reindex` — verified by
    `backend/tests/test_dashboard_executive.py` (7 testes).

### Nota de implementação (ajuste vs. a proposta)

A proposta falava em "variação vs período anterior POR MÉTRICA" e um
`?compare=1` no summary. Na implementação, o delta período-a-período ficou
no headline (`pass_rate_trend` no novo endpoint `/metrics/dashboard`, com
`period_pass_rate` — janela atual vs anterior de mesmo tamanho via
`_results_where` estendido com `until`), exibido no KPI card de Pass rate.
Alertas e ações recomendadas NÃO são lógica nova: reutilizam
`audit.collect_findings` (bad → alertas, bad+warn → ações reformuladas),
evitando duplicar as regras que o Auditor já tem. Top problemas
(`metrics.top_problems`) agrega `automation_report` + `defects_report`.

### Maturity → MVP (acrescentar)

- Dashboard executivo: variação de pass rate vs período anterior, alertas
  de risco, top problemas, ações recomendadas (por regra), última
  atualização.
