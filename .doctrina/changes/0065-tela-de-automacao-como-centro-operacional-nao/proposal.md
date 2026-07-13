# Change 0065-tela-de-automacao-como-centro-operacional-nao — Tela de Automacao como centro operacional (nao formulario de config): separar em abas Configurar/Executar/Historico. Mostrar ultimos runs com status, tempo medio, falhas e ultima execucao. Deixar claro o que e setup e o que e operacao. Empty state melhor com instrucao util.

- **Status:** proposed
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** local-automation

## Why

Tela de Automacao como centro operacional (nao formulario de config): separar em abas Configurar/Executar/Historico. Mostrar ultimos runs com status, tempo medio, falhas e ultima execucao. Deixar claro o que e setup e o que e operacao. Empty state melhor com instrucao util.

## What

Reorganiza a tela de Automação (`Automation.tsx`) de formulário de config
para centro operacional, em 3 abas com papéis claros:

- **Configurar** (setup): targets locais (`automation_targets`), editor de
  `.env`, token do GitHub, catálogo de variáveis — o que é feito uma vez.
- **Executar** (operação): disparo do run local (feature/tag) e do workflow
  GitHub (feature/tag/ambiente/navegador/repositório), com o terminal ao
  vivo — o dia a dia.
- **Histórico** (observabilidade): últimos runs com status, duração, tempo
  médio, falhas e última execução por origem — dados que
  `GET /metrics/automation` e as execuções `origin != manual` já têm;
  reutilizar `automation_report` para o resumo (respeitando
  `ci_monitoring.name_pattern`, ver skill
  novo-consumidor-repassa-config-do-helper).
- **Empty states úteis** por aba: sem target → instrução de configurar; sem
  runs → instrução de executar o primeiro.

## Scope boundaries

Não muda o runner (`runner.py`), o client do GitHub (`ci.py`) nem os
endpoints de execução — é reorganização de UI + um agregado de resumo que
reutiliza os reports existentes. O monitoramento por repositório continua
no Dashboard (capability reporting); o Histórico aqui é operacional (runs
recentes), não o painel gerencial.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
