# Tasks — Change 0062-design-system-orientacao-e-navegacao-assistida

- [x] `CommandPalette` (`CommandPalette.tsx`): busca via `GET /search`,
      navegação por teclado (↑↓/Enter/Esc), ações rápidas.
- [x] `App.tsx`: listener global Ctrl/Cmd+K, estado `cmdkOpen`, ações
      rápidas (novo CT, nova execução, reindex), trigger no header.
- [x] CSS `.cmdk*` (overlay top-centered, input-first, footer de atalhos) +
      `.cmdk-trigger` no header.
- [x] Breadcrumbs nos back-bars (execução/requisito/CT — criar/detalhe):
      "Seção / ID"; CSS `.back-bar`/`.crumbs`/`.crumb-sep`.
- [x] `.content-narrow` (largura de leitura) aplicado no Profile; `.editor`
      já capava.
- [x] `npm run build` limpo; smoke real (SPA 200, CSS do cmdk empacotado,
      `/search` que a paleta consome devolve resultado navegável).
- [x] Spec design-system: critério #4 → verified; Implementation partial →
      verified; versão 0.3.0 → 0.4.0.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-16-0062-design-system-orientacao-e-navegacao-assistida/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
