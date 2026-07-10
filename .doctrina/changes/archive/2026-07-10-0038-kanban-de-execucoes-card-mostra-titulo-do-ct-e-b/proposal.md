# Change 0038-kanban-de-execucoes-card-mostra-titulo-do-ct-e-b — kanban de execucoes: card mostra titulo do CT e barra de progresso de % de passos aprovados, alem do id; permitir vincular/desvincular um defeito ja existente (criado separadamente) a um resultado via API dedicada; edicao do resultado abre como modal centralizado com botao X para fechar em vez de painel inline abaixo do kanban

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** executions, defects

## Why

kanban de execucoes: card mostra titulo do CT e barra de progresso de % de passos aprovados, alem do id; permitir vincular/desvincular um defeito ja existente (criado separadamente) a um resultado via API dedicada; edicao do resultado abre como modal centralizado com botao X para fechar em vez de painel inline abaixo do kanban

## What

- **frontend/src/components/Executions.tsx**
  - Card do Kanban: além do `testcase_id`, mostra o título do CT (via mapa já
    carregado de `api.testcases()`) e, quando há passos estruturados, uma
    barra de progresso (`stepsPassedPct`, derivada de `result.steps` —
    nenhum campo novo no backend).
  - `ResultPanel` passa a abrir dentro de `Modal` (título = id + nome do CT,
    botão X no header, fechável por Esc/backdrop/"Fechar" no footer) em vez
    de inline abaixo do Kanban.
  - Seção "Defeitos": cada defeito vinculado ganha "desvincular"; botão
    "Vincular defeito existente" abre um picker (`api.defects()`) que exclui
    os já vinculados.
- **frontend/src/components/Modal.tsx** — pilha de modais abertos (`openModalIds`)
  para que Esc feche só o do topo; necessário porque "Criar defeito" agora
  pode abrir DENTRO do modal de resultado (primeiro caso de modal aninhado
  no código) e o listener de Esc antigo fechava os dois de uma vez.
- **backend/arbites/executions.py** — `unlink_defect` (espelha `link_defect`).
- **backend/arbites/api.py** — `DefectLinkIn`;
  `POST /executions/{id}/results/{ct}/defects` (valida o defeito via
  `_find_path`, 404 se não existe) e
  `DELETE /executions/{id}/results/{ct}/defects/{defect_id}`.
- **executions spec** e **defects spec** MODIFIED (deltas) + critérios novos.

## Scope boundaries

- Não muda o schema de `Defect` nem adiciona campos novos ao `execution.json`
  — a % de progresso é derivada no frontend a partir de `steps[]` já existente.
- Não implementa busca/filtro no picker de defeitos (lista simples via
  `GET /defects`); não adiciona paginação.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (121 testes backend + build frontend, `tsc --noEmit` incluso).
- [x] Smoke HTTP end-to-end contra servidor real (`python -m arbites serve`): CT →
      execution → marcar passo → criar defeito avulso → vincular → desvincular →
      404 em defeito inexistente. Sem tooling de browser neste ambiente Windows
      para screenshot; o React foi verificado por `tsc` + build + smoke da API
      que ele consome, não por captura visual.
- [x] Critérios novos citam `backend/tests/test_executions.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
