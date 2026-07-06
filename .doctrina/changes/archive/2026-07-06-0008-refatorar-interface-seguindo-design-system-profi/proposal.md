# Change 0008-refatorar-interface-seguindo-design-system-profi — refatorar interface seguindo Design System profissional (AppShell, grid 8px, tipografia, cards, formularios 12 col, sidebar vertical, kanban, empty states, acessibilidade WCAG AA)

- **Status:** applied
- **Applied:** 2026-07-06
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** (none — chore)

## Why

refatorar interface seguindo Design System profissional (AppShell, grid 8px, tipografia, cards, formularios 12 col, sidebar vertical, kanban, empty states, acessibilidade WCAG AA)

Backfilled from working-tree changes (frontend only — ver "Scope boundaries"
para os arquivos de backend/0007 que o working-tree também continha):
- `frontend/src/styles.css`
- `frontend/src/App.tsx`
- `frontend/src/components/Automation.tsx`
- `frontend/src/components/Dashboard.tsx`
- `frontend/src/components/Executions.tsx`
- `frontend/src/components/TestCaseEditor.tsx`
- `frontend/src/components/Warnings.tsx`
- `frontend/src/components/XrayImport.tsx`

## What

Refatoração puramente apresentacional do frontend (React + Vite), sem mudança
de comportamento, contratos de API ou dados. Introduz um Design System coeso
(tema dark enterprise no estilo Jira/Xray/GitHub Projects/Linear):

- **AppShell** — header fixo de 56px, sidebar fixa de 240px, main com padding de
  24px; nada renderiza sob o header (`frontend/src/App.tsx`, `styles.css`).
- **Grid & tipografia** — escala de espaçamento 8/16/24/32/48px em tokens;
  escala tipográfica H1 24 · H2 20 · H3 16 · Body 14 · Caption 12; fonte única.
- **Sidebar vertical** — antiga fileira horizontal de abas virou nav vertical
  com estados hover/seleção e badge de contagem.
- **Cards / Dashboard** — KPIs de mesma altura (padding 16, raio 8), header sem
  sobreposição (`.page-head`), gráfico em card, empty states.
- **Formulários** — inputs/botões de altura fixa 36px, labels acima, grid
  responsivo de 12 colunas; variantes de botão Primary/Secondary/Danger.
- **Execuções** — kanban em grid de 6 colunas, barra de progresso, contadores
  em destaque.
- **Automação** — Targets, run local e GitHub Actions em cards distintos.
- **Acessibilidade** — foco visível (`:focus-visible`), contraste WCAG AA,
  nenhum texto abaixo de 12px, status sempre dot+texto.

Arquivos tocados por esta change (apenas frontend):
`frontend/src/styles.css`, `frontend/src/App.tsx`,
`frontend/src/components/{Dashboard,Executions,Automation,TestCaseEditor,Warnings,XrayImport}.tsx`.

## Scope boundaries

- **Não** altera comportamento, endpoints ou schemas do backend. Os arquivos
  `backend/arbites/api.py`, `backend/arbites/ai.py`, `backend/tests/*` e a change
  `0007-m5-ia-opcional-*` que apareceram no backfill do working-tree pertencem à
  change 0007 (M5 IA opcional), em andamento em paralelo — **não** fazem parte
  desta chore.
- **Não** cria capability/spec nova: a UI é uma visualização da estrutura em
  disco (product.md) e não possui critérios EARS próprios; por isso é chore.
- **Não** adiciona fontes externas (mantém stack de sistema, coerente com o
  princípio local/offline).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Frontend typecheck + build passam (`npm --prefix frontend run build` = `tsc --noEmit && vite build`) — build OK em ~2.3s.
- [x] Backend intacto: `python -m pytest backend/tests -q` verde (66 passed; nenhum arquivo de backend tocado por esta change).
- [x] Chore sem spec: nenhuma capability afetada, portanto sem critérios EARS a cobrir (`doctrina coverage` inalterado).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
