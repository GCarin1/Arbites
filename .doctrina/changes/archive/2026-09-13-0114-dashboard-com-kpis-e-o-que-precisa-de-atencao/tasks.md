# Tasks — Change 0114-dashboard-com-kpis-e-o-que-precisa-de-atencao

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Linha de indicadores no topo do dashboard, com health score junto dos demais números.
- [x] Bloco "O que precisa de atenção" logo abaixo, com síntese, riscos e ações recomendadas.
- [x] Degradação sem IA: o bloco usa os alertas e ações determinísticos de `GET /metrics/dashboard`.
- [x] `backend/tests/test_dashboard_attention.py` provando o contexto do bloco e o dashboard com a IA desligada.
- [x] Estilos da linha de KPIs e do bloco de atenção, sem criar componente canônico novo.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0114-dashboard-com-kpis-e-o-que-precisa-de-atencao/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
