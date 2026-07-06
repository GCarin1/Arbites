# Tasks — Change 0008-refatorar-interface-seguindo-design-system-profi

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Reescrever `frontend/src/styles.css` como Design System (tokens, grid 8px, escala tipográfica, cards, controles 36px, sidebar, kanban, empty states, foco visível).
- [x] `App.tsx` — AppShell (header 56px, sidebar 240px, main 24px) e nav vertical com estados hover/seleção.
- [x] `Dashboard.tsx` — `.page-head` sem sobreposição, KPIs de mesma altura, gráfico em card, empty states.
- [x] `Executions.tsx` — header sem sobreposição, kanban em grid, barra de progresso e contadores em destaque.
- [x] `Automation.tsx` — Targets, run local e GitHub Actions em cards distintos.
- [x] `TestCaseEditor.tsx` / `XrayImport.tsx` / `Warnings.tsx` — formulários em grid de 12 col, tabelas com scroll, caminho de arquivo legível, empty states.
- [x] Confirmar build limpo (`npm --prefix frontend run build`).

## Closing steps

- [x] Apply the change: chore sem deltas — `doctrina change apply` marcou como applied.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-06-0008-refatorar-interface-seguindo-design-system-profi/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
