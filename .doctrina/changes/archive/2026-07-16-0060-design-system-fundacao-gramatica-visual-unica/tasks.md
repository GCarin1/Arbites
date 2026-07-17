# Tasks — Change 0060-design-system-fundacao-gramatica-visual-unica

- [x] Auditar `styles.css` + componentes: inventariadas as variações. Achado:
      botão/input/badge JÁ canônicos (`button`+`.primary`, seletor de input,
      `status-dot`+`--dot`); card divergia (4 defs repetindo a superfície,
      `.chart-card` sem sombra, `.todo-card` padding one-off) e havia ~12
      margens mágicas inline em cards.
- [x] Botão primário/secundário/destrutivo: confirmados canônicos
      (`button`/`button.primary`/`button.danger`) — decidido NÃO renomear
      para `.btn-*` (criaria dois sistemas; ver nota no delta).
- [x] Input canônico: confirmado (seletor de elemento, `--h-control`,
      focus/disabled consistentes) — sem mudança necessária.
- [x] Consolidar `.card`: UMA regra de superfície compartilhada por
      `.card`/`.metric-card`/`.chart-card`/`.todo-card`; variantes só com o
      que as diferencia. Corrigido: chart-card ganha sombra, todo-card vai a
      `--s2`.
- [x] Badge de status: confirmado `status-dot` + `--dot` como o componente
      único — sem mudança.
- [x] Hierarquia: título de página `--fs-h1`/700 (era `--fs-h2`); `.subtitle`
      leve; `.block` (`--s3`) como ritmo de blocos por token, 12 margens
      inline convertidas.
- [x] 1 CTA por bloco: varredura confirmou o padrão já seguido (toolbars têm
      no máximo um `primary`; secundários neutros) — sem mudança.
- [x] `npm run build` limpo; smoke real (SPA 200, CSS consolidado servido);
      revisão visual documentada.
- [x] Spec design-system: Implementation planned → partial, Status → active,
      critérios #1/#2 → verified; versão 0.1.0 → 0.2.0.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-16-0060-design-system-fundacao-gramatica-visual-unica/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
