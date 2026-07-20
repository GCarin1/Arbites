# Change 0080-tela-hoje-landing-com-visao-do-dia — tela hoje: landing com visao do dia

- **Status:** applied
- **Applied:** 2026-07-20
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** home

## Why

O app abre em Test cases — uma lista fria, sem "situação agora".
O QA precisa abrir 4 abas para saber se há run rodando, defeito novo,
afazer de hoje ou daily pendente.

## What

- Nova aba **Hoje** (primeira do menu, default ao abrir): cards de runs
  ativos (`GET /runs/active`), últimas executions, defeitos abertos,
  afazeres do dia, daily do dia (feita/pendente) e problemas.
- Composição 100% frontend sobre endpoints existentes; cada card navega
  para a aba correspondente; falha de uma fonte não derruba a tela.
- Workspace vazio → empty state de primeiro uso (epic → story → CT).
- Segue o design system (skill `design-system-canonico`).

## Scope boundaries

- Nenhum endpoint novo no backend.
- Não duplica o dashboard (sem métricas/gráficos — só estado operacional).
- Não é configurável na v1 (cards fixos).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] App abre na aba Hoje; cards compostos e navegáveis; empty state de primeiro uso; falha isolada por card — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
