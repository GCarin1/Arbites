# Change 0021-afazeres-mencoes-na-descricao-e-os-chips-de-link — afazeres: mencoes @ na descricao e os chips de link viram hiperlinks clicaveis que navegam ate o item (CT/requisito/execucao/todo), inferindo a aba pelo prefixo do id

- **Status:** applied
- **Applied:** 2026-07-07
- **Date:** 2026-07-07
- **Owner:**
- **Affects specs:** (none — chore)

## Why

afazeres: mencoes @ na descricao e os chips de link viram hiperlinks clicaveis que navegam ate o item (CT/requisito/execucao/todo), inferindo a aba pelo prefixo do id

## What

- **App.tsx** — `navigateTo(id)`: infere a aba pelo prefixo do id
  (CT→Test cases, EP/ST→Requisitos, EXEC→Execuções, TD→Afazeres) e seleciona o
  artefato. Passado ao `Todos` como `onNavigate`.
- **ReadView.tsx** — `DocBody` aceita `onMention`; quando presente, as menções
  `@ID` no corpo viram botões `.mention-link` que navegam até o item.
- **Todos.tsx** — os chips de link viram `button.link-chip-btn` clicáveis
  (navegam; desabilitados quando o link é pendente/inexistente) e a descrição
  expandida usa `DocBody onMention={onNavigate}`.
- **styles.css** — estilos de `.mention-link` (link inline) e `link-chip-btn`.

## Scope boundaries

- Só frontend/navegação; sem backend, dados ou spec.
- Defeitos (DF-) não têm view dedicada → menção/link a defeito não navega.
- Link pendente (id inexistente) fica desabilitado (não navega para tela de erro).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (build do frontend + pytest 88).
- [x] Navegação é UI-only; sem impacto em specs/critérios.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
