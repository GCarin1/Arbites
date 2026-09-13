# Change 0135-barra-sub-abas-ia-transborda — barra de sub-abas da IA transborda a viewport em 390px: a aba Configuracao fica cortada na borda direita sem nenhum sinal de rolagem

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** runtime (uncertain; signals: configuracao)
- **Affects specs:** design-system

## Why

barra de sub-abas da IA transborda a viewport em 390px: a aba Configuracao fica cortada na borda direita sem nenhum sinal de rolagem

## What

A faixa de abas (`.tab-bar`) usa `display: flex` sem rolagem: em 390 px as
quatro abas da IA (Gerar · Revisar · Context Pack · Configuração) somam mais
que a largura disponível e a última é cortada na borda do quadro, sem barra
de rolagem, sem reticências e sem qualquer sinal de que há mais conteúdo. A
aba existe, é alcançável por teclado, mas ninguém que olhe a tela sabe disso.
O mesmo vale para a faixa de Automação (Histórico · Executar · Configurar),
que hoje cabe por sorte de rótulo curto.

O conserto é um componente único em vez de dois `map` soltos:

- `frontend/src/components/TabBar.tsx` (novo) — a faixa de abas canônica,
  com `role="tablist"`, rolagem horizontal quando não cabe e a aba ativa
  trazida para dentro do campo de visão a cada troca.
- `frontend/src/styles.css` — `.tab-bar` ganha `overflow-x: auto`, abas que
  não encolhem (`flex: 0 0 auto`) e **sombra de rolagem** pela técnica de
  `background-attachment: local/scroll`: a sombra aparece só no lado onde
  ainda há aba escondida, e some sozinha quando a faixa inteira cabe. Sem
  JavaScript de medição.
- `AiAssist.tsx` e `Automation.tsx` passam a montar a faixa pelo componente.

**Afeta spec:** `design-system` — o critério 8 já promete que nada transborda
em 390 px e que o que é largo por natureza rola dentro do próprio bloco. A
faixa de abas corta em vez de rolar: o delta acrescenta o requisito explícito
e o critério que o prova.

## Scope boundaries

- Não mexe no conteúdo de nenhuma aba, só na faixa que as lista.
- Não toca nas outras quatro quebras de layout em 390 px relatadas na mesma
  leva (período do ciclo, heatmap do perfil, árvore de requisitos, passos do
  modal de resultado) — cada uma tem a sua change.
- Não introduz medição por JavaScript nem `ResizeObserver`: a sombra de
  rolagem é CSS puro.

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
- [x] Em 390 px, na tela de IA, a caixa da aba "Configuração" cabe inteira
      dentro da faixa depois de rolar, e a faixa mostra sombra do lado que
      ainda esconde aba — medido no navegador (`scrollWidth` da faixa maior
      que `clientWidth`) e conferido na captura.
- [x] Em 1440 px a faixa continua sem rolagem e sem sombra — a mesma medição
      no desktop devolve `scrollWidth === clientWidth`.

## Open questions

Nenhuma.
