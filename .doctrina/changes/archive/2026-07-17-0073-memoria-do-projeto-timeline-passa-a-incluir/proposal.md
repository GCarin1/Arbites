# Change 0073-memoria-do-projeto-timeline-passa-a-incluir — Memoria do Projeto: timeline passa a incluir criacao de caso de teste (testcases.created) e mudancas de resultado dentro de executions (result_events: CT passou/falhou/bloqueado em EXEC-X) como novos tipos filtraveis; derivado do indice existente, sem persistencia nova

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** project-memory

## Why

Memoria do Projeto: timeline passa a incluir criacao de caso de teste (testcases.created) e mudancas de resultado dentro de executions (result_events: CT passou/falhou/bloqueado em EXEC-X) como novos tipos filtraveis; derivado do indice existente, sem persistencia nova

## What

`GET /memory/timeline` ganha 2 tipos novos derivados do índice:
`testcase` (criação de CT — `testcases.created`, análogo ao de
requisito) e `result` (mudança de resultado dentro de execution —
`result_events`: "CT-X passou/falhou/bloqueou em EXEC-Y", com data do
evento). Filtros da UI ganham os 2 tipos; `Memory.tsx` atualiza rótulos e
dots. Sem persistência nova — tudo já está indexado.

## Scope boundaries

result_events podem ser muitos: o tipo `result` entra no filtro DESLIGADO
por default (opt-in) para não afogar a timeline; limite global mantido.
Não altera as chamadas de IA (recap) — só a tela.

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
