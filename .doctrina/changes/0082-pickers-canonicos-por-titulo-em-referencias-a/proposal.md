# Change 0082-pickers-canonicos-por-titulo-em-referencias-a — pickers canonicos por titulo em referencias a entidades

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** design-system

## Why

Os `<datalist>` casam pelo ID — quem não decora `ST-0042` não acha
nada. O `SingleRefInput` (busca id+título via `GET /search`) já existe e é
superior, mas não é usado em todo lugar.

## What

- Regra no design system: referência a entidade (epic/story/CT/execution/
  defeito) usa **`SingleRefInput`** (id+título), nunca `<datalist>` por ID.
- Varredura e troca dos pontos que usam datalist/select cru para entidade
  (Context Pack epic/story, e demais ocorrências encontradas no sweep).
- Squad (string livre, não entidade) permanece com datalist.
- Skill `design-system-canonico` ganha o item.

## Scope boundaries

- Não muda `GET /search` (já busca por título).
- Não converte selects de valores fixos (status/prioridade/kind).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Nenhuma referência a entidade via datalist-por-ID restante (grep); Context Pack e demais pontos usando SingleRefInput — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
