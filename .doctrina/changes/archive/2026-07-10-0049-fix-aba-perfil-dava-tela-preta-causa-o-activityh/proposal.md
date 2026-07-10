# Change 0049-fix-aba-perfil-dava-tela-preta-causa-o-activityh — fix: aba Perfil dava tela preta. Causa: o ActivityHeatmap fazia [...data.years] e a resposta do backend nao-reiniciado (shape 0047, sem o campo years) deixava years=undefined -> TypeError no render -> React desmontava o app (fundo escuro = tela preta); erro so aparecia no console do browser, nao nos logs. Fix: guardar data.years com ?? [] e adicionar um ErrorBoundary keyado por aba para que o crash de UMA view nunca derrube o app inteiro

- **Status:** applied
- **Applied:** 2026-07-10
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** (none — chore)

## Why

fix: aba Perfil dava tela preta. Causa: o ActivityHeatmap fazia [...data.years] e a resposta do backend nao-reiniciado (shape 0047, sem o campo years) deixava years=undefined -> TypeError no render -> React desmontava o app (fundo escuro = tela preta); erro so aparecia no console do browser, nao nos logs. Fix: guardar data.years com ?? [] e adicionar um ErrorBoundary keyado por aba para que o crash de UMA view nunca derrube o app inteiro

## What

Bug: clicar em Perfil deixava a tela preta, sem nada nos logs de back nem de
front. Era um **crash de render do React** (erro de runtime do browser → só no
console, não em logs de servidor); com o app sem ErrorBoundary, o React 18
desmonta a árvore inteira e sobra o fundo escuro = "tela preta".

Causa direta: `ActivityHeatmap` fazia `[...data.years]`. Quando o backend NÃO
foi reiniciado após a change 0048, ele responde no shape antigo (0047) sem o
campo `years` — e o FastAPI ignora o `?year=` desconhecido, então a chamada
retorna 200 (nenhum erro no back). No front, `years` fica `undefined` e
`[...undefined]` estoura `TypeError`.

- **frontend/src/components/ActivityHeatmap.tsx** — `data.years ?? []` e
  `data.totals?.[metric] ?? 0` (resiliente a resposta parcial/antiga).
- **frontend/src/components/ErrorBoundary.tsx** (novo) — captura erros de
  render e mostra uma mensagem, mantendo menu e demais abas utilizáveis.
- **frontend/src/App.tsx** — envolve o conteúdo principal em
  `<ErrorBoundary key={tab}>` (trocar de aba remonta e limpa o erro).

## Scope boundaries

- Chore de frontend; sem mudança de contrato/endpoint (o backend 0048 já
  devolve `years`). O fix torna o front robusto a skew de versão front↔back e
  a qualquer crash de view.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build frontend verde (`tsc --noEmit`); causa-raiz demonstrada por simulação da resposta sem `years`.
- [x] Chore UI-only; sem critérios de spec.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
