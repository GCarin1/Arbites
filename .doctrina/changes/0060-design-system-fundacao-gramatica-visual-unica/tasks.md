# Tasks — Change 0060-design-system-fundacao-gramatica-visual-unica

- [ ] Auditar `styles.css` + componentes: inventariar variações atuais de
      botão, input, card e badge (onde divergem).
- [ ] Definir `.btn-primary` / `.btn-secondary` canônicos (cor/altura/raio)
      e trocar botões ad-hoc pelas classes nas telas.
- [ ] Definir input canônico (altura/focus/disabled) e aplicar nos formulários.
- [ ] Consolidar `.card` (padding/borda); migrar `.chart-card`/`.todo-card`
      para herdar a base, removendo bordas duplicadas.
- [ ] Fixar o badge de status (`status-dot` + rótulo) como componente único.
- [ ] Rever hierarquia: pesos de título/subtítulo, tamanho card principal vs
      secundário, espaçamento entre blocos.
- [ ] Varrer telas: garantir no máximo 1 CTA de destaque por bloco.
- [ ] `npm run build` limpo; revisão visual das telas afetadas.
- [ ] Atualizar spec design-system: Implementation planned → partial,
      critérios #1/#2 → verified.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0060-design-system-fundacao-gramatica-visual-unica/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
