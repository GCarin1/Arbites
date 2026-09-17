# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

```ops
bump-version minor
append-requirement ubiquitous: The system shall apresentar toda série temporal com a escala do eixo de valores, as datas do primeiro e do último ponto, e uma frase que descreva a faixa e o extremo em linguagem corrente.
append-requirement unwanted: The system shall not resolver densidade de pontos com rolagem lateral dentro do gráfico; a área de acerto cresce na altura, porque um gráfico que só se vê por pedaços nunca é lido inteiro.
append-criterion [verified] A série mostra mínimo, máximo e as duas datas, descreve-se em uma frase, não rola lateralmente e não corta o ponto extremo contra a borda; série sem variação mostra um valor só — verified by `frontend/scripts/audita-estreito.mjs` e verificação em navegador.
```
