# Change 0064-test-cases-como-produto-de-rastreabilidade-nao — Test cases como produto de rastreabilidade (nao explorer de arquivos): busca fixa no topo; filtros por status, tag, prioridade, automacao e requisito; contagem visivel por pasta; badges de status mais claros; painel lateral de detalhes ao clicar num CT; acoes rapidas sem abrir a tela inteira.

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** testcases

## Why

Test cases como produto de rastreabilidade (nao explorer de arquivos): busca fixa no topo; filtros por status, tag, prioridade, automacao e requisito; contagem visivel por pasta; badges de status mais claros; painel lateral de detalhes ao clicar num CT; acoes rapidas sem abrir a tela inteira.

## What

Evolui o repositório de CTs (`TcRepository.tsx`/`Tree.tsx`) de "explorer de
arquivos" para produto de rastreabilidade:

- **Busca fixa no topo** da árvore (filtra por ID/título, client-side sobre
  o `GET /testcases` já carregado; realça e expande pastas com match).
- **Filtros combinados**: status, tag, prioridade, tipo/automação e
  requisito (story) — o backend `GET /testcases` já filtra por parte disso;
  completar os params que faltarem e expor todos na UI.
- **Contagem por pasta**: nº de CTs (e nº filtrado quando há filtro ativo)
  visível em cada nó da árvore.
- **Badges de status mais claros**: usar o badge canônico (design-system
  0060) na linha do CT — status + prioridade + automação de relance.
- **Painel lateral de detalhes**: clicar num CT abre painel à direita
  (título, status, story, tags, últimos resultados, defeitos ligados) SEM
  sair da árvore — o editor completo continua a um clique.
- **Ações rápidas no painel**: mudar status, abrir editor, copiar ID —
  sem navegar para a tela inteira.

## Scope boundaries

Não muda o modelo de dados nem o formato dos arquivos `.md` (capability
`workspace-core` intocada). Não remove o editor atual — o painel lateral é
um atalho, não um substituto. Drag-and-drop e CRUD de pastas ficam como
estão. Os badges dependem da gramática da change 0060 (se 0060 não landou,
usar as classes atuais e migrar depois).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
