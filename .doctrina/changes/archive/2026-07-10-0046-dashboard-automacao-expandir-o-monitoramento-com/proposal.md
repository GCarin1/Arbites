# Change 0046-dashboard-automacao-expandir-o-monitoramento-com — dashboard automacao: expandir o monitoramento com (1) ranking de CTs que mais falham nos runs de automacao, (2) sparkline dos runs recentes por repo, (3) contagem de CTs flaky por repo + lista global de flaky, (4) MTTR (tempo ate voltar ao verde) e quebrado-desde por repo, (5) filtro por ambiente no GET /metrics/automation e dropdown na Dashboard

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** reporting

## Why

dashboard automacao: expandir o monitoramento com (1) ranking de CTs que mais falham nos runs de automacao, (2) sparkline dos runs recentes por repo, (3) contagem de CTs flaky por repo + lista global de flaky, (4) MTTR (tempo ate voltar ao verde) e quebrado-desde por repo, (5) filtro por ambiente no GET /metrics/automation e dropdown na Dashboard

## What

Follow-ups pedidos sobre o monitoramento de automação (change 0045), todos
sobre a mesma base (execuções `origin != manual`, sem novo dado no backend):

- **backend/arbites/metrics.py** — `automation_report` ganha uma 2ª query (por
  resultado) para: `top_failing_testcases` (CTs que mais falham, pior-primeiro,
  com repos e taxa) e flaky por repo/global (CT que passou E falhou nos runs do
  repo). `_mttr_and_broken` calcula o MTTR (média das durações falha→verde) e
  `broken_since` quando o repo termina vermelho. Cada repo ganha `recent`
  (sparkline dos últimos runs). Novo parâmetro `env` filtra por ambiente,
  mantendo `envs` completo para o seletor.
- **backend/arbites/api.py** — `GET /metrics/automation?days=&env=`.
- **frontend** — types estendidos, `api.metricsAutomation(days, env)`, e a seção
  da Dashboard ganha: dropdown de ambiente (recarrega só a seção), colunas
  Recentes (sparkline), MTTR, Flaky e Estado ("quebrado há Nd"), sub-tabela
  "Casos que mais falham (automação)" e a lista de flaky. CSS do sparkline
  (`.run-cell.*`) e do cabeçalho de seção com controle (`.section-head`).
- **reporting spec** MODIFIED (delta) + critério [verified] #9.

Genérico como o resto: nenhuma referência a empresa/organização/projeto.

## Scope boundaries

- Sparkline usa os últimos 12 runs; MTTR trata "verde" = `passed` (qualquer
  outro desfecho mantém vermelho). Não há ainda gráfico temporal contínuo por
  repo — o sparkline cobre a leitura rápida de tendência.
- Sem novo dado persistido: tudo derivado de `results[]`/nome da execução.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (147 testes backend + build frontend).
- [x] Critério #9 do reporting cita `backend/tests/test_automation_report.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
