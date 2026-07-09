# Change 0028-afazeres-substituir-a-tabela-por-layout-de-cards — afazeres: substituir a tabela por layout de cards/blocos estilo sticky notes, preservando selecao multipla, expandir descricao, status rapido, links clicaveis, prazo com atraso e acoes

- **Status:** applied
- **Applied:** 2026-07-09
- **Date:** 2026-07-09
- **Owner:**
- **Affects specs:** (none — chore)

## Why

afazeres: substituir a tabela por layout de cards/blocos estilo sticky notes, preservando selecao multipla, expandir descricao, status rapido, links clicaveis, prazo com atraso e acoes

## What

- **Todos.tsx** — a tabela de afazeres vira um grid de **cards estilo sticky
  notes** (doc §1.4): borda lateral colorida por status (open/doing/blocked/
  done), título clicável expande a descrição no próprio card, checkbox de
  seleção múltipla, status rápido, prazo com destaque de atraso, chips de link
  clicáveis e ações Editar/Excluir. Toda a funcionalidade existente preservada
  (bulk delete com modal, edit desabilitado com >1 selecionado, menções @).
- **styles.css** — tokens `.todo-cards`/`.todo-card*` (grid responsivo
  auto-fill 280px, done com opacidade reduzida).

## Scope boundaries

- UI-only; sem mudança de API/dados/spec (capability `todos` intacta).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build do frontend + pytest 105 verdes.
- [x] Chore UI; critérios de `todos` seguem cobertos (funcionalidade preservada).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
