---
name: leitura-agrupada-em-card
description: Como estruturar telas de leitura no frontend Arbites — agrupar metadados num card com cabeçalho (título/status/ações), evitando campos flutuantes sobre o fundo.
when: Ao criar ou revisar qualquer visão read-only (detalhe de entidade, painel de metadados) no frontend; quando campos aparecem soltos sobre o fundo ou com hierarquia visual fraca.
---

# Skill — leitura-agrupada-em-card

## When to use this skill

- Vai construir/ajustar uma tela de **detalhe/leitura** de uma entidade
  (test case, requisito, defeito, execução) em `frontend/src/components/`.
- Um review aponta "campos flutuantes", "tela inacabada", "muito fundo
  vazio", "hierarquia fraca" ou "ações desconectadas".
- Um bloco (ex.: "Corpo") já está num card e os metadados acima **não** —
  inconsistência visual.

## Princípio

Informação relacionada tem que **parecer** relacionada: um grupo de
metadados precisa de container (borda + background levemente distinto do
fundo + padding), com o título da entidade e as **ações no cabeçalho do
card**. Nunca renderizar rótulos/valores soltos direto sobre `--bg`. Modelo
mental: Jira / GitHub Issues / Azure DevOps — "detail card" com header.

## Procedure

1. Use o componente compartilhado `DetailCard`
   (`frontend/src/components/ReadView.tsx`): props `id`, `title`, `status`,
   `actions` (Editar/Excluir no header) e o grid de metadados como children.
2. Metadados como `ReadField` (rótulo caption + valor) dentro de
   `.read-grid` (grid responsivo de 12 col → 3–4 por linha). Ações que
   afetam a entidade ficam **no header do card**, perto do contexto — nunca
   soltas no topo da página.
3. Contraste: card em `--surface`, header em `--surface-2`, sobre o fundo
   `--bg`; padding 16px (`--s2`), raio 8px (`--r-card`). Reuse os tokens,
   não invente medidas.
4. Consistência: se o corpo/descrição está num card, os metadados também
   devem estar — dois cards irmãos (detalhes + corpo), não card + campos
   soltos.
5. Modo edição pode manter `h2` + `toolbar` + formulário; o **modo leitura**
   é que usa o `DetailCard`. Ao salvar, volte para leitura (change 0011).

## Anti-patterns

- `ReadField`/rótulos soltos direto sobre o fundo da página, sem container.
- Botão "Excluir" no topo da página, longe da entidade que afeta — aproxime
  do contexto (header do card).
- Poucos campos espalhados por toda a largura (muito espaço vazio) em vez de
  um grid denso de 3–4 colunas.
- Um bloco com card e o resto sem — tratamentos visuais misturados na mesma
  tela.

## Related material

- `frontend/src/components/ReadView.tsx` — `DetailCard`, `ReadField`, `DocBody`.
- `frontend/src/styles.css` — tokens `.detail-card*`, `.read-grid`, `.card`.
- Changes 0008 (AppShell/tokens), 0011 (modo leitura), 0012 (este card).
