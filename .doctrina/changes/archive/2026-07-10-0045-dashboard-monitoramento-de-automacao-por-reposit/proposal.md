# Change 0045-dashboard-monitoramento-de-automacao-por-reposit — dashboard: monitoramento de automacao por repositorio. Novo GET /metrics/automation agrega execucoes de automacao (origin != manual) agrupadas por repositorio extraido do NOME da execucao via regex configuravel (ci_monitoring.name_pattern em arbites.yaml; default generico <nome> <sep> <repo>.<env> sem citar empresa/projeto), com pass/fail por run derivado dos resultados, ranking pior-primeiro (repos que mais falham), quebra por ambiente e contagem de runs fora do padrao. Nova secao na Dashboard

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** reporting

## Why

dashboard: monitoramento de automacao por repositorio. Novo GET /metrics/automation agrega execucoes de automacao (origin != manual) agrupadas por repositorio extraido do NOME da execucao via regex configuravel (ci_monitoring.name_pattern em arbites.yaml; default generico <nome> <sep> <repo>.<env> sem citar empresa/projeto), com pass/fail por run derivado dos resultados, ranking pior-primeiro (repos que mais falham), quebra por ambiente e contagem de runs fora do padrao. Nova secao na Dashboard

## What

O usuário quer monitorar as execuções de automação (que rodam via GitHub
Actions, uma por repositório) no dashboard: quais repos passam, quais falham
com mais frequência. O nome de cada run já codifica repo+ambiente (ex.:
"Regression . <org>/<repo>.cer"), mas esse formato é específico da
instituição — então a extração é por **regex configurável**, com um default
genérico (nenhuma string de empresa/projeto no código).

- **backend/arbites/metrics.py** — `DEFAULT_CI_NAME_PATTERN` (regex genérica
  `<nome> <sep> <repo>.<env>`); `_run_outcome` (desfecho de um run a partir
  dos seus `results[]`); `automation_report(conn, name_pattern, days)` que
  agrupa execuções `origin != manual` por repo, ordena pior-primeiro, quebra
  por ambiente e conta `unparsed`. Regex inválida cai no default e reporta
  `pattern_error` (não derruba a rota).
- **backend/arbites/api.py** — `GET /metrics/automation?days=` lendo
  `ci_monitoring.name_pattern` do `arbites.yaml`.
- **frontend** — types `AutomationReport`/`AutomationRepoRow`,
  `api.metricsAutomation`, e a seção "Automação por repositório" na Dashboard
  (`AutomationPanel`): tiles de passaram/falharam/pass-rate, tabela
  pior-primeiro, e um hint explicando `ci_monitoring.name_pattern` quando nada
  casa o padrão ou a regex é inválida.
- **reporting spec** MODIFIED (delta) + critério [verified] #8.

## Fonte de dados & acesso ao GitHub

O dashboard agrega o que JÁ está no Arbites (execution.json coletados) — não
faz chamadas novas ao GitHub. O acesso à org do GitHub só importa para o
fluxo de coleta de CI já existente (dispatch/collect), não para esta métrica.

## Scope boundaries

- Genérico por princípio: nenhuma referência a empresa/organização/projeto no
  código, spec ou default do padrão.
- Não implementa (ainda) tendência de pass-rate por repo no tempo, ranking de
  CTs que mais falham, nem MTTR — ficam como follow-ups óbvios sobre a mesma
  base.
- Não muda a coleta de CI (ver `ci-automation`); só lê o que foi coletado.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (143 testes backend + build frontend).
- [x] Critério #8 do reporting cita `backend/tests/test_automation_report.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
