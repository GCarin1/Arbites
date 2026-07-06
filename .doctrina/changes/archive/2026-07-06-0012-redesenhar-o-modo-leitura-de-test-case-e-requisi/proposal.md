# Change 0012-redesenhar-o-modo-leitura-de-test-case-e-requisi — redesenhar o modo leitura de test case e requisito: agrupar os metadados (Tipo, Prioridade, Status, Story, Tags, Arquivo) num card de detalhes com cabecalho contendo titulo/status e as acoes Editar/Excluir, com contraste de fundo e grid responsivo, eliminando a sensacao de campos flutuantes

- **Status:** applied
- **Applied:** 2026-07-06
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** (none — chore)

## Why

redesenhar o modo leitura de test case e requisito: agrupar os metadados (Tipo, Prioridade, Status, Story, Tags, Arquivo) num card de detalhes com cabecalho contendo titulo/status e as acoes Editar/Excluir, com contraste de fundo e grid responsivo, eliminando a sensacao de campos flutuantes

## What

Redesign presentacional do **modo leitura** de test case e requisito: os
metadados deixam de flutuar sobre o fundo e passam a um **card de detalhes**
com cabeçalho (id/título + status + ações Editar/Excluir) e corpo com o grid
de metadados; o "Corpo" segue num card irmão. Elimina a sensação de campos
soltos e a inconsistência (antes só o Corpo tinha card).

- `frontend/src/components/ReadView.tsx` — novo `DetailCard` (header com
  título/status/ações + body com children).
- `frontend/src/styles.css` — tokens `.detail-card`, `.detail-card-head`
  (fundo `--surface-2` p/ contraste), `.detail-title`, `.detail-actions`,
  `.detail-card-body`; `.read-grid` sem margem dentro do card.
- `frontend/src/components/TestCaseEditor.tsx` e
  `Requirements.tsx` (`RequirementEditor`) — modo leitura usa `DetailCard` +
  card de Corpo; ações movidas para o header do card; modo edição segue com
  h2 + toolbar + formulário.

## Scope boundaries

- **Não** altera API, dados nem o modo edição (só a apresentação do modo
  leitura).
- **Não** cria capability/spec (a UI é visualização; chore, como 0008/0011).
- Reusa os tokens do design system — nenhuma medida arbitrária nova.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (tsc + vite build + pytest).
- [x] Modo leitura de CT e requisito renderiza `DetailCard` (metadados agrupados, ações no header) + card de Corpo; modo edição intacto.
- [x] Chore sem spec: nenhuma capability afetada (`doctrina coverage` inalterado).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
