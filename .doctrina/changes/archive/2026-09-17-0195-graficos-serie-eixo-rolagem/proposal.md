# Change 0195-graficos-serie-eixo-rolagem — o gráfico que não dizia nada

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** design-system

## Why

*"Vários campos de gráfico sem detalhes, não me informa eixo x nem y, só sei o
final. Se você fosse uma pessoa não técnica, entenderia esses gráficos?"*

Não entenderia. Três coisas faltavam, e juntas faziam o desenho não informar:

1. **Sem escala.** A linha é normalizada entre o mínimo e o máximo da própria
   série, então subir de 12 para 13 tem **exatamente o mesmo desenho** de
   subir de 12 para 1200. Só o valor final aparecia, e ele sozinho não diz de
   onde veio.
2. **Sem tempo.** "Como cada medida se moveu" sem dizer entre quando e quando.
3. **Rolagem lateral dentro do cartão.** Ela existia para dar espaço aos
   pontos clicáveis (change 0181) e cobrava um preço alto demais: um gráfico
   que só se vê por pedaços nunca é lido inteiro.

## What

- Escala do eixo de valores (mínimo e máximo) à esquerda, fora do SVG —
  texto dentro de um `viewBox` esticado sairia deformado.
- Data do primeiro e do último ponto embaixo.
- Uma frase por série: *"Entre 29 e 48 em 45 execuções — o maior foi em 05 de
  set."* É ela que responde a escala para quem não desenha gráfico na cabeça.
- **A rolagem saiu.** Os pontos deixam de ser botões de 16px disputando
  largura e viram uma faixa invisível de altura inteira por ponto: a área de
  acerto cresce na dimensão que sobra. Restam círculos desenhados — marcas,
  não alvos —, destacados nos extremos e no último (rótulo direto seletivo).
- Margem no `viewBox` nos dois eixos: o ponto da ponta saía cortado ao meio,
  e é justamente ele que mais se olha.
- Série sem variação mostra **um** valor na escala: repetir "9" em cima e
  embaixo sugere um intervalo que não existe.

## Scope boundaries

A exceção "Equivalente" da WCAG 2.5.8 continua declarada no código: com
dezenas de pontos a faixa fica estreita, e a tabela *Execuções recentes* abre
a mesma descida em linha de altura cheia.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] Navegador com 45 execuções: dez séries com escala, datas e frase, sem
      rolagem lateral e sem ponto cortado.
- [x] `audita-estreito.mjs` em 390px: 15 telas, nenhum achado.

## Open questions

Nenhuma.
