# Tasks — Change 0045

- [x] `metrics.automation_report` + `DEFAULT_CI_NAME_PATTERN` (genérico) + `_run_outcome`.
- [x] `GET /metrics/automation?days=` lendo `ci_monitoring.name_pattern` da config.
- [x] Frontend: `AutomationReport`/`AutomationRepoRow` types + `api.metricsAutomation`.
- [x] Frontend: seção "Automação por repositório" na Dashboard (`AutomationPanel`),
      com tiles passaram/falharam/pass-rate, tabela pior-primeiro e hint de config
      quando nada parseia / regex inválida.
- [x] Testes backend (agrupamento pior-primeiro, ignora manual + unparsed, padrão
      custom, regex inválida não derruba, vazio) + suíte verde + build.
- [x] Smoke HTTP contra servidor real com o formato EXATO do usuário
      ("Regression . <org>/<repo>.cer") — parse, ranking e env corretos.

## Closing steps

- [x] Apply: merge delta na spec reporting.
- [x] Archive.
- [x] Update index.json.
