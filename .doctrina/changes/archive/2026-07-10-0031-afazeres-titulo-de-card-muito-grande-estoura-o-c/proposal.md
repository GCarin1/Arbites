# Change 0031-afazeres-titulo-de-card-muito-grande-estoura-o-c — afazeres: titulo de card muito grande estoura o card (overflow-wrap:anywhere cresce verticalmente) — truncar com line-clamp e reticencias sem aumentar o card; tooltip com o titulo completo

- **Status:** applied
- **Applied:** 2026-07-10
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** (none — chore)

## Why

afazeres: titulo de card muito grande estoura o card (overflow-wrap:anywhere cresce verticalmente) — truncar com line-clamp e reticencias sem aumentar o card; tooltip com o titulo completo

## What

- **styles.css** — `.todo-card-title` passa a truncar em 2 linhas com reticências
  (`display:-webkit-box; -webkit-line-clamp:2; overflow:hidden`), mantendo
  `overflow-wrap:anywhere` só p/ tokens longos. O card não cresce mais com o título.
- **Todos.tsx** — `title={t.title}` no botão do título (tooltip com o texto completo).

## Scope boundaries

- UI-only; sem backend/spec.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build do frontend verde.
- [x] Chore UI; skill truncar-titulo-em-card criada.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
