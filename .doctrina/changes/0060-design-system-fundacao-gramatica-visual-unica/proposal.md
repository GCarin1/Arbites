# Change 0060-design-system-fundacao-gramatica-visual-unica — Design system - fundacao: gramatica visual unica. Botao primario (cor/altura/raio fixos) e secundario padronizados; input com altura e comportamento unicos; card com padding e borda unicos; badge com linguagem de status unica. Hierarquia visual: titulos mais fortes, subtitulos mais leves, cards principais maiores e secundarios menores, mais espaco entre blocos, menos bordas repetidas. Uma unica acao de destaque (CTA dominante) por bloco; acoes secundarias discretas.

- **Status:** proposed
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** design-system

## Why

Design system - fundacao: gramatica visual unica. Botao primario (cor/altura/raio fixos) e secundario padronizados; input com altura e comportamento unicos; card com padding e borda unicos; badge com linguagem de status unica. Hierarquia visual: titulos mais fortes, subtitulos mais leves, cards principais maiores e secundarios menores, mais espaco entre blocos, menos bordas repetidas. Uma unica acao de destaque (CTA dominante) por bloco; acoes secundarias discretas.

## What

Fundação do design-system (primeira das 3 slices; as demais 0061/0062
dependem desta). Toca `frontend/src/styles.css` (classes canônicas) e
padroniza os componentes que já existem, sem reescrever features:

- **Botão primário/secundário**: uma classe cada (`.btn-primary`,
  `.btn-secondary`) com cor/altura (`--h-control`)/raio (`--r-control`)
  fixos; auditar as telas e trocar botões ad-hoc pela classe canônica.
- **Input**: classe única com altura e comportamento (focus, disabled)
  consistentes.
- **Card**: padding interno e borda únicos (`.card` canônico) — hoje há
  `.chart-card`, `.todo-card`, `.card` com bordas repetidas; consolidar.
- **Badge de status**: uma linguagem só (o padrão `status-dot` + texto já
  existe; fixar como o componente de status oficial e eliminar variações).
- **Hierarquia**: revisar `--fs-h1/h2/h3` e pesos; cards principais maiores
  que secundários; espaçamento entre blocos; remover bordas duplicadas.
- **CTA dominante**: convenção de no máximo 1 ação de destaque por bloco;
  varrer telas com vários botões de mesmo peso.

Provável extração de um `frontend/src/components/ui/` (Button, Input, Card,
Badge) ou consolidação via classes CSS — a decidir na implementação.

## Scope boundaries

Não muda lógica de nenhuma tela (só a camada visual). Não introduz tema
claro (fica no Future do spec). Não mexe na navegação/estados (são as slices
0061/0062). Não altera contratos de API.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
