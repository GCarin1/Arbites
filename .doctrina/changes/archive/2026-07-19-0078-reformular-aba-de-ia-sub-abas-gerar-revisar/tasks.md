# Tasks — Change 0078-reformular-aba-de-ia-sub-abas-gerar-revisar

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `AiAssist.tsx`: barra de sub-abas interna (Gerar · Revisar · Context Pack · Configuração), abre em Gerar; estado `tab` como os outros componentes de abas.
- [x] Seletor de provider global no cabeçalho; `GenerateCard`/`ReviewCard` recebem `provider` por prop e removem o dropdown próprio (`ProviderSelect` fica só na config, se necessário).
- [x] Contexto ativo + histórico de interações acompanham as abas de trabalho (Gerar/Revisar); Configuração hospeda `ProvidersCard`.
- [x] Reutilizar os estilos de sub-abas do design system (mesmo padrão da Automação); um `primary` por bloco.
- [x] `npm run build` limpo; revisão visual das 4 sub-abas + provider global aplicado a gerar/revisar/negativos.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-19-0078-reformular-aba-de-ia-sub-abas-gerar-revisar/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
