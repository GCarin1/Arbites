# Change 0011-editores-de-test-case-e-requisito-epic-story-dev — editores de test case e requisito (epic/story) devem abrir em modo leitura apos salvar, com botao Editar para voltar ao modo de edicao, em vez de ficar sempre em modo de edicao

- **Status:** applied
- **Applied:** 2026-07-06
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** (none — chore)

## Why

editores de test case e requisito (epic/story) devem abrir em modo leitura apos salvar, com botao Editar para voltar ao modo de edicao, em vez de ficar sempre em modo de edicao

## What

Introduz um **modo leitura** nos editores de test case e de requisito
(epic/story). Antes o painel abria sempre em modo edição (todos os campos como
inputs) e permanecia assim após salvar. Agora:

- Ao selecionar um item (ou logo após criá-lo), o painel abre em **modo
  leitura**: campos como valores read-only (`ReadField`) e o corpo renderizado
  (`DocBody` — render leve de markdown, sem dependência externa).
- Botão **Editar** entra no modo edição (o formulário existente, incl. o toggle
  Formulário/Markdown cru do test case).
- **Salvar** persiste e **volta ao modo leitura**; **Cancelar** descarta as
  edições não salvas (recarrega do backend) e volta à leitura.

Arquivos:
- `frontend/src/components/ReadView.tsx` (novo) — `ReadField` + `DocBody`.
- `frontend/src/components/TestCaseEditor.tsx` — estado `editing`, load
  reutilizável, view read-only.
- `frontend/src/components/Requirements.tsx` (`RequirementEditor`) — idem.
- `frontend/src/styles.css` — tokens de leitura (`.read-grid`, `.read-field`,
  `.doc-body`).

## Scope boundaries

- **Não** altera API, payloads de save nem validações — só a camada de UI
  (qual visão o painel mostra).
- **Não** adiciona biblioteca de markdown; `DocBody` é um render mínimo
  (cabeçalhos, linhas, parágrafos) que constrói só nós de texto (sem HTML
  injetável).
- **Não** mexe no board de Execuções nem nos wizards (Xray/Automação), que já
  têm seus próprios fluxos.
- Itens recém-criados abrem em leitura mostrando "Sem conteúdo — clique em
  Editar", coerente com o pedido.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (tsc + vite build + pytest).
- [x] Fluxo manual conferido no código: selecionar/criar → leitura; Editar → edição; Salvar/Cancelar → volta à leitura.
- [x] Chore sem spec: nenhuma capability afetada (`doctrina coverage` inalterado).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
