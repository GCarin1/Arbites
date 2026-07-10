---
name: grade-de-quadrados-responsiva-e-tooltip-no-cursor
description: Para uma grade de quadrados (heatmap/calendário) preencher um container e escalar com ele, use colunas flex:1 + células aspect-ratio:1 (não px fixos). E um tooltip que segue o cursor precisa de position:fixed com clientX/clientY — dentro de um ancestral position:relative, coordenadas de viewport ficam deslocadas.
when: Ao construir um heatmap/calendário de contribuições, grade de células quadradas, ou qualquer tooltip flutuante que deva aparecer na posição do mouse.
---

# Skill — grade-de-quadrados-responsiva-e-tooltip-no-cursor

## When to use this skill

- Vai montar um heatmap estilo GitHub / calendário de células quadradas que
  deve **preencher** o card em vez de ficar pequeno num canto.
- Vai mostrar um tooltip que aparece **onde o mouse está** sobre a célula.

## Preencher o container com quadrados que escalam

Células de tamanho fixo (`width: 11px`) deixam a grade pequena num container
largo. Para escalar com o container:

1. **Colunas flexíveis:** o container das colunas é `display:flex`; cada coluna
   `flex: 1; min-width: 0`. Assim N colunas dividem a largura disponível.
2. **Células quadradas por proporção:** a célula é `width: 100%` (preenche a
   coluna) + `aspect-ratio: 1 / 1` (altura segue a largura). Container maior →
   coluna mais larga → célula maior, sempre quadrada. Sem JS de medição.
3. **Rótulos alinhados como IRMÃOS flex:** a linha de meses e a coluna de dias
   da semana usam a MESMA estrutura flex (mesmos `gap`, mesmo nº de slots) que
   a grade, para alinharem sem cálculo de pixel. A coluna de dias ganha um
   `padding-top` igual à altura da linha de meses.
4. Legenda/exemplos fora da grade precisam **desligar** o `aspect-ratio`/
   `width:100%` (senão explodem no flex): `.legenda .cell { width:12px;
   height:12px; aspect-ratio:auto; flex:0 0 auto }`.

## Tooltip que segue o cursor

`clientX/clientY` são coordenadas de **viewport**. Se o tooltip é filho de um
elemento `position: relative`, `left/top` passam a ser relativos a ESSE
elemento — o tooltip aparece deslocado.

- **Use `position: fixed`** no tooltip: aí `left: clientX; top: clientY`
  casam com o viewport, independentemente de ancestrais posicionados.
- Adicione um pequeno offset (`transform: translate(14px,14px)`) para não
  ficar embaixo do cursor, e `pointer-events: none` para não piscar/roubar o
  hover.
- Atualize a posição no `onMouseMove` (não só `onMouseEnter`) para o tooltip
  acompanhar o movimento dentro da mesma célula.

## Anti-patterns

- Grade de `px` fixos "centralizada" que deixa metade do card vazio.
- Medir largura com `ResizeObserver`/JS quando `flex:1 + aspect-ratio` resolve
  em CSS puro.
- Tooltip `position:absolute` dentro de um card `position:relative` usando
  `clientX/clientY` → aparece no lugar errado.
- Reusar a classe da célula na legenda sem resetar `aspect-ratio`/`width`.

## Related material

- `frontend/src/components/ActivityHeatmap.tsx` — grade + tooltip (`heatmap-tip`).
- `frontend/src/styles.css` — `.heatmap*`, `.heatmap-cell` (aspect-ratio),
  `.heatmap-tip` (position:fixed), `.heatmap-legend .heatmap-cell` (reset).
- Spec `reporting` (#11). Relacionada: [[formato-especifico-do-usuario-vira-config-regex]].
