# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

Medir o `scrollWidth` da PÁGINA foi o único teste de tela estreita que estas
telas passaram durante várias changes — e elas quebravam assim mesmo, porque
o que quebra de verdade em 390px passa por baixo desse número.

```ops
append-requirement ubiquitous: The system shall manter, em tela de 320 a 390 px, todo texto dentro do seu contêiner, nenhum rótulo escrito por cima do valor que ele nomeia, e nenhum controle com alvo de toque abaixo de 24 CSS px — salvo exceção declarada no próprio elemento, com o caminho equivalente nomeado.
append-requirement ubiquitous: The system shall empilhar as tabelas de dado em tela estreita, com cada linha virando cartão e cada célula carregando o rótulo da sua coluna, em vez de rolar de lado.
append-requirement unwanted: The system shall not tratar o estouro horizontal da página como prova de layout responsivo; a verificação percorre as telas medindo texto cortado, rótulo sobreposto, corte pelo ancestral e alvo de toque.
append-criterion [verified] As quinze telas do menu, incluindo as cinco faixas da observabilidade, não acusam nenhum achado a 390 px nem a 320 px no detector `frontend/scripts/audita-estreito.mjs`; e o detector, com a causa reintroduzida por CSS injetado, volta a acusar o rótulo sobreposto — verified by `frontend/scripts/audita-estreito.mjs`.
set-header Last updated: 2026-09-16
bump-version minor
```
