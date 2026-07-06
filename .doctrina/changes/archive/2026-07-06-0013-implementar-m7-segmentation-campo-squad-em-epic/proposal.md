# Change 0013-implementar-m7-segmentation-campo-squad-em-epic — implementar M7 segmentation: campo squad em epic/story, CT e execucao; heranca do squad efetivo do CT (CT -> story -> epic); indice do squad; filtro por squad em /testcases, /executions e /metrics; endpoint de squads; filtro no board do Kanban e no dashboard

- **Status:** proposed
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** segmentation

## Why

implementar M7 segmentation: campo squad em epic/story, CT e execucao; heranca do squad efetivo do CT (CT -> story -> epic); indice do squad; filtro por squad em /testcases, /executions e /metrics; endpoint de squads; filtro no board do Kanban e no dashboard

## What

- **indexer.py** — colunas `squad` (requirements, testcases, executions) e
  `squad_effective` (testcases), com migração tolerante; `_recompute_effective_squads`
  materializa a herança CT → story → epic via UPDATE único (chamado no reindex
  completo e no incremental quando um requisito/CT muda).
- **api.py** — `squad` nos models de requisito/CT/execução; filtro `squad`
  em `GET /testcases` (por `squad_effective`), `GET /requirements`,
  `GET /executions` e nos `/metrics/*`; novo `GET /squads` (declarados no
  arbites.yaml + distintos no índice).
- **metrics.py** — parâmetro `squad` nas 7 métricas + matriz; recorte por
  `squad_effective` do CT (e squad efetivo da story em requirement_coverage).
- **executions.py** — `squad` no execution.json.
- **Frontend** — campo squad nos editores de CT (com "herdado" no modo leitura)
  e requisito; chip de filtro por squad no **board do Kanban** (mapa CT→squad
  efetivo, filtra colunas/contadores/progresso) e no **dashboard** (dropdown que
  recalcula métricas/matriz/export); squad na criação de execução.
- **Testes** — `backend/tests/test_segmentation.py` (herança/override, filtro
  de CT, base do filtro do board, /squads, dashboard por squad, retrocompat).

## Scope boundaries

- Squad é rótulo de agrupamento, **não** controle de acesso (o produto segue
  single-user local).
- O filtro do board é por **squad efetivo do CT** (o pedido do usuário: CTs de
  squads diferentes numa mesma execução); o squad da própria execução é
  metadado secundário.
- Warning para squad fora de uma lista declarada em `arbites.yaml` fica no
  *Optional* da spec (não implementado neste MVP).
- Metas/thresholds e painel de defeitos por squad são M8/M9 (deltas de
  `reporting`), fora desta change.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde — pytest (73, inclui os 6 de `test_segmentation.py`) + build do frontend (tsc + vite).
- [x] Os 4 critérios da spec `segmentation` verificados com evidência em `backend/tests/test_segmentation.py` (`doctrina coverage`).
- [x] Retrocompatibilidade: suíte inteira (73) verde, workspace sem squad intacto.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
