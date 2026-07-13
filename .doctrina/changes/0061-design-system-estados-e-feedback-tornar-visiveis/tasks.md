# Tasks — Change 0061-design-system-estados-e-feedback-tornar-visiveis

- [ ] Componente `Toast`/`useToast` (confirmação "salvo" transitória) e
      aplicar nos saves das telas (CT, requisito, defeito, decisão, todo…).
- [ ] Skeleton/spinner canônico; substituir os "Carregando…" ad-hoc.
- [ ] Padrão `.field-error` — erro perto da ação; auditar onde só o banner
      global aparece hoje.
- [ ] Auditar todos os empty states → padrão `.empty-state` com instrução
      útil (o que fazer para sair do vazio).
- [ ] Hook `useDirty` p/ modais e formulários: sinal visual de não-salvo +
      confirmação ao fechar descartando.
- [ ] Revisão de textos: encurtar blocos longos onde a UI já explica;
      tooltip canônico para ajuda pontual.
- [ ] `npm run build` limpo; revisão visual documentada das telas afetadas.
- [ ] Atualizar spec design-system: critério #3 → verified.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0061-design-system-estados-e-feedback-tornar-visiveis/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
