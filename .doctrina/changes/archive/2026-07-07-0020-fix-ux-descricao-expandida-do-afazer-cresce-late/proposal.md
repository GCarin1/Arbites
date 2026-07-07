# Change 0020-fix-ux-descricao-expandida-do-afazer-cresce-late — fix ux: descricao expandida do afazer cresce lateralmente (scroll horizontal) em vez de quebrar linha e expandir para baixo — a celula dentro da tabela com overflow-x nao quebrava tokens longos

- **Status:** applied
- **Applied:** 2026-07-07
- **Date:** 2026-07-07
- **Owner:**
- **Affects specs:** (none — chore)

## Why

fix ux: descricao expandida do afazer cresce lateralmente (scroll horizontal) em vez de quebrar linha e expandir para baixo — a celula dentro da tabela com overflow-x nao quebrava tokens longos

## What

- **styles.css** — `.todo-desc-row td` e `.doc-body` ganham
  `overflow-wrap: anywhere` (+ `word-break: break-word`, `white-space: normal`).
  A descrição expandida vive numa célula de uma tabela `auto-layout` dentro de
  `.table-wrap { overflow-x: auto }`; um trecho longo/sem espaços elevava a
  min-content-width da célula e a tabela crescia lateralmente (scroll
  horizontal, altura ~2 linhas). Com `overflow-wrap: anywhere` a min-content da
  célula vai a ~0, a tabela deixa de crescer por causa da descrição, e o texto
  se limita à largura visível e **expande para baixo**.

## Scope boundaries

- Correção de CSS/UX; sem mudança de comportamento de dados ou spec.
- `overflow-wrap: anywhere` no `.doc-body` global é seguro (só quebra quando o
  token estouraria a largura) e beneficia também os modos leitura de CT/requisito
  e o contexto da daily.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (build do frontend + pytest 88).
- [x] Fix é CSS-only; sem impacto em specs/critérios.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
