# Tasks — Change 0155-aba-observabilidade-eixo-temporal

- [x] Criar a aba e o esqueleto com seletor de período e comparação.
- [x] Série temporal por sinal, com meta e direção declaradas.
- [x] Descida do agregado até a run, o job e o anexo.
- [x] Bloco "o que mudou": regressão de sinal contra o período anterior,
      quebra depois de sequência verde, silêncio da ingestão e run que
      chegou sem manifesto.
- [ ] NÃO entregue: "teste que virou instável". Instabilidade é por
      CENÁRIO, e o manifesto declara MEDIDA agregada — o Arbites não
      recebe o resultado por cenário nesta ingestão. Fazer isso exige o
      Cucumber JSON parseado por cenário, o que é ingestão nova, não um
      bloco de tela. Fica para uma change própria.
- [x] Renderizar a análise em Markdown da run.
- [x] Estados vazios e medição em 390 px e 1440 px.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-14-0155-aba-observabilidade-eixo-temporal/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
