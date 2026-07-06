# Spec Delta — capability: segmentation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/segmentation/spec.md`

---

## Context

M7 implementa a capability de ponta a ponta: campo `squad` em epic/story, CT
e execução; squad efetivo do CT materializado com herança (CT → story →
epic); filtro por squad em `/testcases`, `/executions` e `/metrics/*`;
`GET /squads`; e, no frontend, campo squad nos editores, chip de filtro no
board do Kanban e no dashboard. Isto passa a Implementação de `planned` →
`verified` e os quatro critérios de `[unverified]` → `[verified]`.

## Header (MODIFIED)

- **Implementation:** verified — M7 (backend/arbites/indexer.py,
  backend/arbites/api.py, backend/arbites/metrics.py,
  backend/arbites/executions.py; frontend: Dashboard/Executions/TestCaseEditor/
  Requirements). Herança materializada em `squad_effective` (recalculada no
  reindex completo e incremental).

## Acceptance criteria (MODIFIED — verificados)

1. [verified] Um CT sem squad próprio herda o squad da story; um squad
   explícito no CT prevalece — verified by `backend/tests/test_segmentation.py`.
2. [verified] Filtrar o board de uma execução por squad mostra apenas os
   CTs daquele squad efetivo — verified by `backend/tests/test_segmentation.py`.
3. [verified] Dashboard filtrado por squad recalcula as 7 métricas e a
   matriz sobre o subconjunto — verified by `backend/tests/test_segmentation.py`.
4. [verified] Workspace sem nenhuma squad permanece integralmente
   funcional (retrocompatibilidade) — verified by `backend/tests/test_segmentation.py`.
