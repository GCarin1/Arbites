# Change 0062-design-system-orientacao-e-navegacao-assistida — Design system - orientacao e navegacao assistida: breadcrumbs em areas profundas, header de contexto fixo com rota atual destacada, area de detalhes fixa para item selecionado. Busca global e comandos rapidos (palette), links de acao dentro dos cards. Em telas grandes: limitar largura util, paineis laterais colapsaveis, controlar ritmo vertical.

- **Status:** proposed
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** design-system

## Why

Design system - orientacao e navegacao assistida: breadcrumbs em areas profundas, header de contexto fixo com rota atual destacada, area de detalhes fixa para item selecionado. Busca global e comandos rapidos (palette), links de acao dentro dos cards. Em telas grandes: limitar largura util, paineis laterais colapsaveis, controlar ritmo vertical.

## What

3ª slice do design-system (depende da fundação 0060). Orientação espacial +
navegação assistida + uso do espaço em telas grandes:

- **Breadcrumbs** nas áreas profundas (repositório de CTs dentro de pastas,
  detalhe de execução, editor de requisito) — hoje só existe o botão
  "← Voltar".
- **Header de contexto**: título da seção atual sempre visível; rota atual
  destacada no menu (já existe `.active`; reforçar hierarquia).
- **Busca global** (atalho tipo Ctrl+K): paleta de comandos sobre o
  `GET /search` existente — navegar para qualquer CT/req/execução/defeito/
  decisão de qualquer tela, mais ações rápidas ("nova execução", "novo CT").
- **Links de ação dentro dos cards**: onde um card exibe uma referência
  (CT, execução), ela navega — estender o padrão que Todos/Decisions já têm
  para as demais telas.
- **Telas grandes**: limitar largura útil onde prosa/formulário (max-width
  de leitura), painéis de detalhe colapsáveis, ritmo vertical consistente.

Artefatos prováveis: componente `Breadcrumbs`, componente `CommandPalette`
(reusa `/search`; sem backend novo), classes `.content-narrow`, ajustes no
`App.tsx`/`main-inner`.

## Scope boundaries

Não cria endpoint novo — a busca global usa o `GET /search` que já serve o
autocomplete. Não muda o menu lateral estruturalmente (grupos/pins ficam
como estão). Não é responsividade mobile (fora de escopo da v1).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
