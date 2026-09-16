# Change 0181-revisao-layout-tela-estreita — revisao de layout em tela estreita com detector reutilizavel

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** design-system

## Why

revisao de layout em tela estreita com detector reutilizavel

## What

- `frontend/scripts/audita-estreito.mjs` (novo): percorre as 15 telas do menu
  e as 5 faixas da observabilidade medindo cinco famílias de quebra. Sai com
  código 1 se achar algo, então serve de gate. Playwright não é dependência
  do projeto (`PLAYWRIGHT_ROOT` aponta uma instalação existente).
- **Tabelas**: as três tabelas novas da observabilidade tinham `data-label`
  em cada célula e não tinham a classe `stack-narrow` que LIGA o padrão —
  rolavam de lado em vez de empilhar.
- **Rótulo por cima do valor** (defeito do padrão compartilhado, não só das
  telas novas): `white-space: nowrap` herdado impedia o rótulo de quebrar, e
  em célula `.mono` ele ainda herdava a fonte monoespaçada, bem mais larga.
  Corrigido no `::before` e no valor.
- **Texto cortado**: `.metric-formula` e `.exec-item-msg` trocam a reticência
  por quebra de linha em tela estreita.
- **Alvo de toque**: `padding-block` em link e `link-btn` dentro de célula;
  `min-height` no atalho da evidência.
- **Série de sinal**: dezenas de pontos se espremiam a 3px um do outro (em
  QUALQUER largura); agora a série tem largura mínima proporcional à
  quantidade e rola dentro do cartão.
- `.doctrina/skills/layout-em-tela-estreita.md`: o método.

## Scope boundaries

- O ponto da série continua com 16px de diâmetro: crescê-lo faria os pontos se
  sobreporem. A exceção do WCAG 2.5.8 se aplica (a tabela Execuções recentes
  abre a MESMA descida) e está declarada no elemento, em
  `data-alvo-pequeno`, não escondida no detector.
- Uma série reunir vários repositórios sob o mesmo nome de sinal é questão de
  PRODUTO, não de layout: a rolagem conserta a manipulação, não o fato de a
  linha misturar quatro produtos. Fica registrado abaixo.

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
- [x] 15 telas + 5 faixas sem nenhum achado a 390px e a 320px.
- [x] O detector foi PROVADO: com a causa reintroduzida por CSS injetado ele
      volta a acusar os rótulos sobrepostos; com a correção, nada.

## Open questions

- Um sinal de mesmo nome vindo de vários repositórios vira UMA série: com 4
  produtos × 24 dias, `duracao_suite_s` tem 96 pontos interleavados por tempo,
  e a linha não é a tendência de nada. Separar por repositório (uma linha por
  produto) ou agregar (média por dia) é decisão de produto — os dois mudam o
  que a aba afirma.
