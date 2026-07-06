# Change 0010-substituir-os-window-prompt-window-confirm-nativ — substituir os window.prompt/window.confirm nativos do browser por modais em tela com o design system da aplicacao (novo test case, novo epic/story, novo defeito, confirmacoes de exclusao e de fechar execucao)

- **Status:** applied
- **Applied:** 2026-07-06
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** (none — chore)

## Why

substituir os window.prompt/window.confirm nativos do browser por modais em tela com o design system da aplicacao (novo test case, novo epic/story, novo defeito, confirmacoes de exclusao e de fechar execucao)

## What

Troca puramente apresentacional: os diálogos nativos do browser
(`window.prompt`/`window.confirm`) foram substituídos por modais em tela com
o design system da aplicação. Comportamento e chamadas de API idênticos.

- `frontend/src/components/Modal.tsx` (novo) — `Modal` reutilizável (overlay,
  painel, header com título + fechar, footer) e `ConfirmModal` de conveniência.
  Fecha com Esc e clique no backdrop, trava o scroll do body, devolve o foco
  ao elemento anterior, `role="dialog"` + `aria-modal`, foco inicial no
  primeiro campo.
- `frontend/src/styles.css` — tokens de modal (overlay, painel, header/body/
  footer) com as mesmas variáveis de superfície, raio e espaçamento.
- Sites migrados (9 popups nativos → 0):
  - `App.tsx` — "Novo test case" (título + pasta) → `NewTestcaseModal`.
  - `Requirements.tsx` — "Novo epic/story" (título + epic pai) →
    `NewRequirementModal`; confirmação de exclusão → `ConfirmModal`.
  - `Executions.tsx` — "Fechar execução" → `ConfirmModal`; "Criar defeito"
    (título + chave externa) → `NewDefectModal`.
  - `TestCaseEditor.tsx` — confirmação de exclusão → `ConfirmModal`.

## Scope boundaries

- **Não** altera contratos de API, payloads nem fluxos — só a camada de UI
  que coletava os dados. As validações (título obrigatório etc.) seguem as
  mesmas.
- **Não** introduz biblioteca de modal externa (mantém stack local/offline;
  componente próprio, sem portal/dependências novas).
- **Não** toca `XrayImport`/`Automation` (já usavam formulários in-place, sem
  popups nativos).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (tsc + vite build + pytest).
- [x] Nenhum `window.prompt`/`window.confirm`/`window.alert` funcional restante no `frontend/src` (grep só acha comentários no `Modal.tsx`).
- [x] Chore sem spec: nenhuma capability afetada (`doctrina coverage` inalterado).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
