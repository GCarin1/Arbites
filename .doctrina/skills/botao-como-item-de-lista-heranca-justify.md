---
name: botao-como-item-de-lista-heranca-justify
description: Um <button> reestilizado como item de lista/linha herda justify-content:center do estilo base de button — o conteúdo aparece centralizado; sobrescreva para flex-start.
when: Ao usar <button> como linha/item clicável (árvore, lista, célula) reaproveitando classes; ou quando id/título de um item aparece centralizado em vez de à esquerda.
---

# Skill — botao-como-item-de-lista-heranca-justify

## When to use this skill

- Vai transformar um `<button>` num item de lista/linha (repositório, árvore,
  menu) e o conteúdo interno (ícone + texto) precisa ficar à esquerda.
- Bug: "o nome do arquivo/CT/requisito aparece centralizado na linha".

## O bug (real, repositórios)

O estilo base do projeto tem:
```css
button { display: inline-flex; align-items: center; justify-content: center; }
```
`.repo-file-main` era `<button>` com `display: flex` e `flex: 1`, mas **sem**
redefinir `justify-content`. Resultado: herda `center` do estilo base → id +
título centralizados no meio da linha (parecia "centralizado na página").

## Procedure

1. Ao reestilizar um `button` como item de linha, **sobrescreva
   `justify-content: flex-start`** (e `text-align: left`) explicitamente.
2. Regra geral: ao mudar `display` de um elemento que tem estilo base de
   `button`/flex, revise TODAS as props de alinhamento herdadas
   (`justify-content`, `align-items`, `text-align`), não só as que você mudou.
3. Verifique num item com texto curto (o centramento fica óbvio quando sobra
   espaço à direita por causa do `flex: 1`).

## Anti-patterns

- Assumir que `display: flex` num button já alinha à esquerda — o
  `justify-content: center` do estilo base continua valendo.
- "Consertar" com `text-align: left` só (não afeta o eixo principal do flex).

## Related material

- `frontend/src/styles.css` — `.repo-file-main`.
