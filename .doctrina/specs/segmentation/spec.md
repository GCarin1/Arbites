# Spec — segmentation

**Capability:** segmentation
**Status:** active
**Implementation:** verified — M7 (backend/arbites/indexer.py, backend/arbites/api.py, backend/arbites/metrics.py, backend/arbites/executions.py; frontend: Dashboard/Executions/TestCaseEditor/Requirements). Herança materializada em `squad_effective` (recalculada no reindex completo e incremental)
**Realizes:** SC9
**Last updated:** 2026-07-06
**Version:** 0.2.0

## Purpose

Eixo de **squad** que atravessa a cadeia Epic → Story → Test Case →
Execution, permitindo recortar reporte e execução por time. Squad é um
rótulo organizacional/taxonômico — não é controle de acesso (o produto
permanece single-user local). O QA que cobre várias squads passa a poder
marcar cada CT/story com sua squad e filtrar o board e o dashboard por ela,
com as 7 métricas recalculadas sobre o subconjunto.

## Requirements (EARS)

### Ubiquitous

- The system shall aceitar um campo opcional `squad` no frontmatter de
  epic/story (requisito), de test case e no `execution.json`.
- The system shall resolver o **squad efetivo** de um CT por precedência:
  squad explícito no CT → senão herdado da story vinculada → senão do epic
  da story.
- The system shall indexar o squad (bruto e efetivo) no reindex, para
  consultas e filtros O(1).
- The system shall expor a lista de squads conhecidos (definidos em
  `arbites.yaml` mais os distintos presentes no índice) via API, para
  popular os filtros da UI.
- The system shall aceitar `squad` como filtro em `GET /testcases`,
  `GET /executions` e nos endpoints de métricas/matriz (`/metrics/*`).

### Event-driven

- When o usuário filtra o board de execução por squad, the system shall
  exibir no Kanban apenas os resultados cujo CT tem o squad efetivo
  selecionado.
- When o usuário aplica o filtro de squad no dashboard, the system shall
  recalcular as 7 métricas e a matriz de rastreabilidade sobre o
  subconjunto do squad (combinável com os filtros de sprint/epic
  existentes).

### State-driven

- While um CT/story/execução não tem squad e não há herança aplicável, the
  system shall tratá-lo como "sem squad" (bucket explícito) sem quebrar
  nenhuma tela.

### Unwanted-behavior (must-not)

- The system shall not exigir squad: um workspace sem nenhuma squad
  definida continua 100% funcional (campo retrocompatível/opcional).
- The system shall not usar squad como mecanismo de permissão, autenticação
  ou isolamento de acesso — é apenas rótulo de agrupamento.

### Optional

- Where a lista de squads está declarada em `arbites.yaml`, the system may
  emitir warning de integridade para CT/story com squad fora da lista
  (mesma esteira dos warnings existentes).

## Acceptance criteria

1. [verified] Um CT sem squad próprio herda o squad da story; um squad
   explícito no CT prevalece sobre a herança — verified by
   `backend/tests/test_segmentation.py`.
2. [verified] Filtrar o board de uma execução por squad mostra apenas os
   CTs daquele squad efetivo — verified by `backend/tests/test_segmentation.py`.
3. [verified] Dashboard filtrado por squad recalcula as 7 métricas e a
   matriz sobre o subconjunto — verified by `backend/tests/test_segmentation.py`.
4. [verified] Workspace sem nenhuma squad permanece integralmente
   funcional (retrocompatibilidade) — verified by
   `backend/tests/test_segmentation.py`.

## Maturity

**MVP (committed):**

- Campo `squad` em epic/story, CT e execução; herança CT←story←epic;
  índice do squad efetivo; filtro por squad no board e no dashboard
  (métricas + matriz); lista de squads para os filtros da UI.

**Future (aspirational, not committed):**

- Comparativo entre squads lado a lado no dashboard; metas/thresholds por
  squad; squad como agrupador na árvore de CTs.

## Out of scope for this spec

- Squad como controle de acesso/permissão (o produto é single-user local;
  colaboração continua sendo git no workspace).
- Cadastro/gerência de squads como entidade rica (é taxonomia leve:
  `arbites.yaml` + rótulo no frontmatter).
