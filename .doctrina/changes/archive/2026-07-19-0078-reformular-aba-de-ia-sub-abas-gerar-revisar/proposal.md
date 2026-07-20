# Change 0078-reformular-aba-de-ia-sub-abas-gerar-revisar — reformular aba de IA: sub-abas gerar/revisar/context-pack/configuracao e seletor de provider global no topo

- **Status:** applied
- **Applied:** 2026-07-19
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** ai-assist

## Why

A aba de IA empilha numa página só o contexto ativo, gerar, revisar/
negativos, context pack, histórico e a config de providers colapsada — tudo
no mesmo lugar, sem hierarquia clara. E cada card repete seu próprio
dropdown de provider. A tela não deixa claro o que é CONFIGURAÇÃO (setup de
providers/chaves) e o que é TRABALHO (gerar/revisar/exportar), e o ruído de
providers repetidos atrapalha.

## What

- **`AiAssist.tsx`** passa a ter uma barra de sub-abas interna:
  **Gerar · Revisar · Context Pack · Configuração** (mesmo padrão visual da
  tela de Automação). O contexto ativo e o histórico de interações
  acompanham a aba de trabalho; a configuração de providers vira a sub-aba
  Configuração (não mais um botão de toggle).
- **Seletor de provider global** no cabeçalho da tela (um `<select>` único
  no topo), que vale para Gerar, Revisar e Casos negativos — os dropdowns
  por card saem. O Context Pack não usa provider (é export) e a sub-aba
  Configuração define o provider padrão.
- Segue o design system (skill `design-system-canonico`): barra de sub-abas,
  `.card`/`.block`, um `primary` por bloco, badges `status-dot`.

## Scope boundaries

- **Sem mudança de backend** — os endpoints `GET/PUT /ai/providers`,
  `POST /ai/generate-testcases`, `/ai/review/{id}`, `/ai/negative-cases/{id}`
  e o Context Pack permanecem idênticos. É reorganização de UI.
- Não altera a lógica de geração/revisão/preview (preview obrigatório, nada
  gravado sem aceite continua igual).
- Não mexe no fluxo de import por IA (`POST /import/ai`), fora desta tela.
- Não vira duas abas no menu lateral (decisão do usuário: sub-abas na
  própria página).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] `npm run build` limpo; a tela abre em Gerar, alterna entre as 4 sub-abas, e o provider escolhido no topo é usado por gerar/revisar/negativos (revisão visual + smoke dos endpoints já cobertos).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
