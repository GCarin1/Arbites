# Tasks — Change 0046

- [x] `metrics.automation_report`: 2ª query por resultado → `top_failing_testcases` + flaky por repo/global.
- [x] `_mttr_and_broken` (MTTR em horas + `broken_since`) por repo; `recent` (sparkline).
- [x] Filtro `env` (parse do nome), com `envs` sempre completo p/ o dropdown.
- [x] `GET /metrics/automation?env=` no api.py.
- [x] Frontend: types + `api.metricsAutomation(days, env)`; seção com dropdown de ambiente,
      colunas Recentes (sparkline)/MTTR/Flaky/Estado (quebrado desde), sub-tabela "Casos que
      mais falham" e lista de flaky.
- [x] CSS `.run-spark/.run-cell.*` e `.section-head`.
- [x] Testes backend (top failing, flaky por repo, sparkline+MTTR com tempo controlado, env filter)
      + suíte verde (147) + build.
- [x] Smoke HTTP real exercitando as 5 features.

## Closing steps

- [x] Apply: merge delta na spec reporting.
- [x] Archive.
- [x] Update index.json.
