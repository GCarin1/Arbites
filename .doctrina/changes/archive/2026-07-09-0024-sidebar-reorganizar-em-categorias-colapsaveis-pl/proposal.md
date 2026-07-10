# Change 0024-sidebar-reorganizar-em-categorias-colapsaveis-pl — sidebar: reorganizar em categorias colapsaveis (Planejamento, Acompanhamento, Ferramentas, Suporte) com secao Acesso Rapido alimentada por pin/unpin por item (persistido localmente)

- **Status:** applied
- **Applied:** 2026-07-09
- **Date:** 2026-07-09
- **Owner:**
- **Affects specs:** (none — chore)

## Why

sidebar: reorganizar em categorias colapsaveis (Planejamento, Acompanhamento, Ferramentas, Suporte) com secao Acesso Rapido alimentada por pin/unpin por item (persistido localmente)

## What

- **App.tsx** — menu lateral reorganizado em grupos semânticos colapsáveis
  (Planejamento: Requisitos/Test cases/Execuções · Acompanhamento: Afazeres/
  Dashboard/Daily/Reuniões · Ferramentas: Automação/IA/Migração · Suporte:
  Problemas). Cada item tem ação de **pin** (★ no hover); itens fixados aparecem
  na seção **Acesso rápido** no topo. Pins e estado de colapso persistem em
  localStorage (`arbites.pins`, `arbites.navCollapsed`).
- **styles.css** — tokens `.nav-group*`, `.nav-row`, `.nav-pin`.

## Scope boundaries

- UI-only; sem backend/spec. A aba Perfil entra em change própria (D).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build do frontend verde (tsc + vite).
- [x] Chore UI; sem impacto em specs.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
