# Tasks — Change 0077-memoria-do-projeto-agrupar-timeline-por-dia

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `project_memory.timeline`: parâmetros `date_from`/`date_to` (inclusivos, prefixo `YYYY-MM-DD` de `at`) filtrando todas as fontes antes do `limit`.
- [x] `project_memory.timeline_years(conn, kinds)`: anos distintos com eventos (UNION sobre as colunas de data), ordem decrescente.
- [x] API: `GET /memory/timeline` aceita `date_from`/`date_to`; novo `GET /memory/timeline/years?kinds=`.
- [x] `api.ts`: `memoryTimeline` aceita `date_from`/`date_to`; novo `memoryTimelineYears`.
- [x] `Memory.tsx`: seletor Ano (de `timeline_years` + "Todos") e Mês (Todos/Jan..Dez) → `date_from`/`date_to`; busca textual client-side.
- [x] `Memory.tsx`: agrupar por dia em cabeçalhos colapsáveis (data + contagem); recentes expandidos, antigos colapsados. Segue o design system.
- [x] Testes: `test_project_memory.py` cobrindo recorte por período e `timeline_years`; `npm run build` limpo.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-19-0077-memoria-do-projeto-agrupar-timeline-por-dia/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
