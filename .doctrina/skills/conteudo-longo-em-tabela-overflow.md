---
name: conteudo-longo-em-tabela-overflow
description: Conteúdo longo dentro de tabela auto-layout com overflow-x cresce lateralmente; use overflow-wrap para zerar a min-content e forçar quebra para baixo.
when: Ao renderizar texto livre (descrição, corpo, log) dentro de célula de tabela `.table-wrap`/overflow-x, ou quando um conteúdo expandível provoca scroll horizontal em vez de quebrar linha.
---

# Skill — conteudo-longo-em-tabela-overflow

## When to use this skill

- Vai colocar texto livre (descrição de afazer, corpo, mensagem) numa célula
  `<td>` de uma `table.dense` dentro de `.table-wrap` (que tem
  `overflow-x: auto`).
- Um bug relata "expande para o lado", "scroll horizontal", "fica preso em N
  linhas e não quebra", "estoura a largura da tela".

## Por quê (bug real, change 0020)

A descrição expandida do afazer ficava numa célula de tabela `auto-layout`
dentro de `.table-wrap { overflow-x: auto }`. Um trecho longo/sem espaços
eleva a **min-content-width** da célula; o auto-layout então **alarga a
tabela** (que pode passar do container por causa do `overflow-x`), gerando
scroll horizontal e altura travada em ~2 linhas — em vez de quebrar para baixo.

## Procedure

1. Na célula (e no bloco de texto interno) aplique:
   ```css
   .cell { overflow-wrap: anywhere; word-break: break-word; white-space: normal; }
   ```
   `overflow-wrap: anywhere` é o que importa: zera a min-content-width, então a
   tabela deixa de crescer por causa daquele texto e ele se limita à largura
   visível, expandindo para baixo.
2. `word-break: break-word` é só reforço; **não** basta sozinho — ele não
   reduz a min-content-width (a tabela ainda cresceria).
3. Se **outras** colunas (título/links muito longos) também estouram, trate a
   tabela como um todo (larguras `max-width` por coluna, ou `table-layout: fixed`
   com larguras definidas) — mas não use `fixed` por reflexo, ele iguala colunas.
4. Verifique com um caso real: texto longo com um token sem espaços (URL, caminho,
   `@ID@ID@ID`) deve quebrar para baixo, sem barra horizontal.

## Anti-patterns

- Confiar que "texto quebra sozinho": quebra por espaço, mas um token longo
  fura a largura e, dentro de `overflow-x`, vira scroll lateral.
- `word-break: break-all` global em prosa — quebra no meio de palavras normais,
  fica feio; prefira `overflow-wrap: anywhere` (só quebra quando estouraria).
- Resolver com largura fixa em `vw` (ex.: `calc(100vw - 288px)`): quebra quando
  há sidebar/max-width no container; use `overflow-wrap`, não número mágico.

## Related material

- `frontend/src/styles.css` — `.todo-desc-row td`, `.doc-body`.
- `frontend/src/components/Todos.tsx` — descrição expansível na tabela.
- Change `0020` (arquivada) — o fix.
