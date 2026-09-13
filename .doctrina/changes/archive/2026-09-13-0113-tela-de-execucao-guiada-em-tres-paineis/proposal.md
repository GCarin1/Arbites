# Change 0113-tela-de-execucao-guiada-em-tres-paineis — Tela de execucao guiada em tres paineis

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

Modo sentar e executar: lista de ciclos, casos do ciclo e o caso ativo em tres paineis, com passos marcaveis, evidencia e resultado no mesmo lugar, e um rodape que avanca para o proximo caso sem sair da tela. Complementa o Kanban, que continua servindo para arrastar, mas nao serve para executar vinte casos em sequencia.

## What

- `executions` (spec MODIFIED): o modo guiado ao lado do Kanban, operando
  sobre a mesma execution.
- `frontend/src/components/ExecutionGuided.tsx` (novo): os três painéis e o
  rodapé que avança.
- `frontend/src/components/Executions.tsx`: a alternância entre Kanban e
  guiado.
- `backend/tests/test_executions_guided.py`: a prova de que a sequência do
  modo guiado grava na mesma execution e para no último caso.
- Nenhum endpoint novo: o modo guiado é uma leitura diferente do que o M1
  já expõe.

## Scope boundaries

- Não remove nem depreca o Kanban: ele continua servindo para arrastar e
  para ver o ciclo inteiro de uma vez.
- Não cria endpoint: tudo que o modo guiado faz já é coberto pela API do M1
  e pelo ciclo da change 0111.
- Não mexe nas máquinas de estado nem no formato do `execution.json`.
- Não cobre execução automatizada, que não tem ninguém sentado marcando
  passo.

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

Nenhuma.
