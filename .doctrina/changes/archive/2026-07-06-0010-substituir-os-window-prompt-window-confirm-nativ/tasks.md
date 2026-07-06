# Tasks — Change 0010-substituir-os-window-prompt-window-confirm-nativ

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Criar `Modal.tsx` (Modal reutilizável + ConfirmModal) com Esc, backdrop, foco e scroll-lock.
- [x] Adicionar tokens de modal ao `styles.css` alinhados ao design system.
- [x] Migrar "Novo test case" (App.tsx) para `NewTestcaseModal`.
- [x] Migrar "Novo epic/story" e exclusão (Requirements.tsx).
- [x] Migrar "Fechar execução" e "Criar defeito" (Executions.tsx).
- [x] Migrar exclusão do TestCaseEditor.tsx.
- [x] Confirmar zero popups nativos e build limpo.

## Closing steps

- [x] Apply the change: chore sem deltas — `doctrina change apply` marca como applied.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-06-0010-substituir-os-window-prompt-window-confirm-nativ/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
