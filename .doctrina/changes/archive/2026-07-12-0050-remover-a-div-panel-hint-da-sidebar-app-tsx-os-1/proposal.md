# Change 0050-remover-a-div-panel-hint-da-sidebar-app-tsx-os-1 — remover a div panel-hint da sidebar (App.tsx): os 12 textos de dica por aba nao agregavam valor e so ocupavam espaco; deixar a sidebar so com o menu de navegacao (nav). CSS orfa (.sidebar .panel/.panel-hint) removida; .sidebar .nav ganha flex:1 pra preencher o espaco que sobrou

- **Status:** applied
- **Applied:** 2026-07-12
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** (none — chore)

## Why

remover a div panel-hint da sidebar (App.tsx): os 12 textos de dica por aba nao agregavam valor e so ocupavam espaco; deixar a sidebar so com o menu de navegacao (nav). CSS orfa (.sidebar .panel/.panel-hint) removida; .sidebar .nav ganha flex:1 pra preencher o espaco que sobrou

## What

- **frontend/src/App.tsx** — removida a `<div className="panel">` inteira
  (12 parágrafos `.panel-hint`, um por aba) abaixo do menu de navegação na
  sidebar. Sobra só o `<nav>`.
- **frontend/src/styles.css** — `.sidebar .panel`/`.sidebar .panel-hint`
  removidos (órfãos); `.sidebar .nav` ganha `flex:1; min-height:0` para
  preencher o espaço (antes tinha `max-height:60vh` + `border-bottom` só
  para dar lugar ao painel de dica, que não existe mais).

## Scope boundaries

- Chore UI-only; não mexe em navegação/roteamento, só remove o texto
  auxiliar e ajusta o preenchimento da sidebar.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build frontend verde (`tsc --noEmit`); zero refs restantes a panel-hint.
- [x] Chore UI-only; sem critérios de spec.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
