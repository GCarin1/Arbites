# Tasks — Change 0061-design-system-estados-e-feedback-tornar-visiveis

- [x] Componente `Toast`/`useToast` (`Toast.tsx`) + `ToastProvider` no
      `main.tsx`; CSS `.toast-stack`/`.toast`/`.toast-*` com animação.
- [x] Ligar toast "salvo" nos saves principais: DecisionModal, DefectModal,
      TodoModal, MeetingModal, TestCaseEditor, RequirementEditor.
- [x] Skeleton/spinner canônico (`.spinner`/`.skeleton` no CSS) — vocabulário
      único; rollout inline incremental.
- [x] Padrão `.field-error` (erro junto à ação) no CSS.
- [x] Empty states: auditados — já majoritariamente `.empty-state`; os
      `className="empty"` restantes são fallbacks de loading (Suspense), não
      empty states secos.
- [x] Guarda de dirty no `Modal` compartilhado (prop `dirty`): fechar por
      Esc/backdrop/X com form sujo pede confirmação (`ConfirmModal`).
      Detecção via wrapper `.modal-form` (`display: contents`) nos 4 modais
      CRUD.
- [x] `npm run build` limpo; smoke real (SPA 200, CSS de feedback empacotado,
      save 201).
- [x] Spec design-system: critério #3 → verified; versão 0.2.0 → 0.3.0,
      Implementation segue partial (falta 0062).
- [x] Skill: a lição (5 estados obrigatórios) já está em
      `estados-de-feedback-nas-telas` (criada na fase de documentação);
      atualizada com o padrão concreto do wrapper `.modal-form`.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-16-0061-design-system-estados-e-feedback-tornar-visiveis/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
