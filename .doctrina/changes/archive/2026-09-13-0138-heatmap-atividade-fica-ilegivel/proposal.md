# Change 0138-heatmap-atividade-fica-ilegivel — heatmap de atividade fica ilegivel em 390px: celula de 2 pixels numa grade de 38px de altura contra coluna de dias de 140px, rotulos de mes amontoados e seletores do cabecalho cortados a 96px

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** reporting

## Why

heatmap de atividade fica ilegivel em 390px: celula de 2 pixels numa grade de 38px de altura contra coluna de dias de 140px, rotulos de mes amontoados e seletores do cabecalho cortados a 96px

## What

A grade do heatmap foi feita para PREENCHER o card: 53 colunas `flex: 1` e
células quadradas por `aspect-ratio` (skill
`grade-de-quadrados-responsiva-e-tooltip-no-cursor`). Isso escala para cima
lindamente e não tem piso nenhum para baixo. Em 390 px o card útil tem 326 px,
sobram 292 px para 53 colunas mais 52 vãos de 4 px — e a célula sai com
**2,0 × 2,0 px**, medido no navegador. A grade inteira fica com 38 px de
altura enquanto a coluna de dias da semana, presa a `min-height: 12px` por
rótulo, fica com 140 px: os dois blocos não têm como alinhar, e o que se vê é
uma tira de poeira ao lado de Seg/Qua/Sex/Dom espalhados. Os dois seletores
do cabeçalho ("Últimos 12 meses", "Toda atividade") caem para 96 px e viram
"Últimos 1…" / "Toda ativ…".

Um quadrado de 2 px não comunica nada. O conserto é dar um PISO à célula e
deixar a grade rolar de lado dentro do card — que é exatamente o que o
GitHub faz no celular:

- `frontend/src/styles.css`
  - `--heat-cell` (10 px) vira o piso: `.heatmap-col` e `.heatmap-month`
    passam a `flex: 1 0 var(--heat-cell)` — crescem no card largo como
    antes, e param de encolher no estreito.
  - `.heatmap-main` ganha rolagem horizontal; a coluna de dias fica de fora
    dela, parada, como cabeçalho de linha.
  - `.heatmap-weekday` perde o `min-height: 12px` que empurrava a coluna de
    dias para 140 px; com o piso de 10 px na célula, `flex: 1` divide a
    altura da grade e os dois blocos voltam a bater linha a linha.
  - `.card-head` quebra linha em tela estreita, para os seletores caberem
    inteiros em vez de virar reticências.
- `.scroll-x` — a rolagem-com-sombra que a faixa de abas estreou na change
  0135 vira utilitário e passa a ser usada pelos dois. Era o mesmo bloco de
  cinco camadas de gradiente escrito duas vezes; agora é um só, e qualquer
  bloco que precise rolar de lado herda o mesmo sinal de borda.

**Afeta spec:** `reporting` — o heatmap é dela; faltava dizer que a grade tem
tamanho mínimo de célula e rola quando não cabe.

## Scope boundaries

- Não muda o dado do heatmap, nem a escala de cor, nem o tooltip.
- Não esconde semanas nem encurta o período em tela estreita: o ano inteiro
  continua lá, rolando.
- Não mexe nos outros cards do perfil (densidade, tema, identidade).

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
- [x] Em 390 px a célula mede ao menos 10 px de lado e a grade rola dentro
      do card (`scrollWidth > clientWidth` em `.heatmap-main`).
- [x] Em 390 px a altura da coluna de dias bate com a altura da grade
      (diferença de no máximo 2 px), que é o que alinha os rótulos.
- [x] Em 390 px os dois seletores do cabeçalho aparecem com a largura do seu
      conteúdo, sem reticências.
- [x] Em 1440 px a célula continua crescendo para preencher o card e a área
      da grade não rola (`scrollWidth === clientWidth`) — o comportamento
      que a grade já tinha.
- [x] Um rótulo de mês que começaria nas duas últimas colunas deixa de ser
      desenhado: ele não teria largura para si e transbordava a área da
      grade. O mês continua na grade, sem legenda.

## Open questions

Nenhuma.

## Nota sobre o gate de documentação

O passo `docs` do `close` barrou esta change apontando `--heat-cell` como
"flag de uma superfície documentada". Não é: `--heat-cell` é uma custom
property de CSS, interna ao bloco `.heatmap`, sem qualquer alcance fora do
`styles.css`. A heurística do gate casa qualquer coisa que comece com `--`,
e todo token de CSS começa com `--` — os tokens que já existem
(`--bp-narrow`, `--s3`, `--density`) não disparam porque não estão no diff
desta change.

Não há documentação de tokens de design em `docs/` nem no `README.md` (que é
guia de instalação), e escrever uma entrada de README para uma variável de
CSS interna seria ruído. A change foi fechada com `--force`, que registra a
lacuna — esta nota é a lacuna registrada por extenso.
