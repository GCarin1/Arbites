# Change 0074-historico-de-resultados-por-ct-endpoint-que — Historico de resultados por CT: endpoint que lista os resultados passados de um caso de teste (execution, status, data, duracao) derivado da tabela results; exibido no painel lateral do repositorio e no editor do CT para responder se ja passou no passado; status-dot do design system

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** testcases

## Why

Historico de resultados por CT: endpoint que lista os resultados passados de um caso de teste (execution, status, data, duracao) derivado da tabela results; exibido no painel lateral do repositorio e no editor do CT para responder se ja passou no passado; status-dot do design system

## What

Novo `GET /testcases/{id}/results`: lista os resultados passados do CT
(execution_id, status, executed_at, duration) da tabela `results` JOIN
executions, mais recente primeiro. UI: seção "Histórico de resultados" no
painel lateral do repositório (0064) e no editor do CT — sequência de
status-dots + tabela curta; responde "já passou no passado?".

## Scope boundaries

Não recalcula nada (leitura de `results`). Não mostra steps das
execuções passadas (link para a execution cobre o drill-down).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
