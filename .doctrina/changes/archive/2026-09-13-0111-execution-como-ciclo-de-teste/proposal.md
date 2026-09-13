# Change 0111-execution-como-ciclo-de-teste — Execution como ciclo de teste

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

Dar ao ciclo a estrutura que hoje falta: sprint deixa de ser texto livre e passa a ter datas de inicio e fim e status de ciclo entre planejado, em andamento e fechado, o que substitui a decisao registrada na ADR 0010. Cabecalho de progresso no padrao do Xray, com barra empilhada por status, contadores grandes e total de casos. Responsavel por caso de teste dentro do ciclo, para dividir uma regressao entre duas ou mais pessoas, aproveitando a autoria por sessao que ja existe.

## What

- ADR 0013 (substitui a 0010 neste ponto): o ciclo é a execution — datas no
  próprio ciclo, `sprint` rebaixada a rótulo, nenhuma entidade nova.
- `executions` (spec MODIFIED): `starts_on`/`ends_on` no ciclo, `assignee`
  por resultado, vocabulário planejado / em andamento / fechado e o
  cabeçalho de progresso.
- `backend/arbites/executions.py`: o período, o responsável e a validação
  de período invertido.
- `backend/arbites/api.py`: `PATCH` aceitando as datas e a rota
  `POST .../results/{ct}/assignee`.
- `backend/arbites/indexer.py`: as colunas novas, com migração tolerante
  (o índice é descartável — ADR 0001).
- `backend/tests/test_execution_cycle.py`: a prova dos três critérios.
- `frontend/src/components/Executions.tsx`: cabeçalho de progresso no
  padrão Xray e o responsável no card.

## Scope boundaries

- Não cria entidade Sprint, nem cadastro de release ou de responsável: a
  ADR 0013 explica por que a execution já é o ciclo.
- Não renomeia `draft` no disco — o vocabulário novo é de exibição.
- Não mexe nas máquinas de estado de resultado nem de documento do CT.
- Não toca na tela de execução guiada (change 0113) nem no dashboard
  (change 0114), que consomem este ciclo mas são outras mudanças.

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

Nenhuma — a única decisão em aberto (entidade Sprint ou não) virou a ADR 0013.
