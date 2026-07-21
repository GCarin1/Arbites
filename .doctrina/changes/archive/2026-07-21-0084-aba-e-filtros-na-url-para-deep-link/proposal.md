# Change 0084-aba-e-filtros-na-url-para-deep-link — aba e filtros na URL para deep-link

- **Status:** applied
- **Applied:** 2026-07-21
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** design-system

## Why

Trocar de aba perde filtros e não dá para compartilhar "o board do
squad X" — as abas são state, não rotas. Deep-link também serve o reporte:
um link que abre a matriz já filtrada.

## What

- Rota por hash (`#/aba?param=...`), sem lib de router: `App.tsx` lê o
  hash no load e o escreve ao trocar aba; back/forward funcionam.
- Filtros principais serializados: squad do dashboard, filtros do
  repositório de CTs, período/tipos da Memória, aba interna da Automação.
- `onNavigate` atualiza o hash (link compartilhável para um card).

## Scope boundaries

- Hash routing simples — sem migrar para react-router.
- Nem todo estado vai para a URL: só aba + filtros de alto valor listados.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Abrir URL com hash restaura aba+filtros; navegar atualiza o hash; back/forward funcionam — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
