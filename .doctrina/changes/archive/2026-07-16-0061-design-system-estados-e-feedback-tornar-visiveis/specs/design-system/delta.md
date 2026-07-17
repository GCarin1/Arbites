# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

Note: 2ª das 3 slices (depende da fundação 0060). Landou → critério #3 →
verified; Implementation segue `partial` (falta a 0062).

---

O que landou (estados & feedback):

### Ubiquitous

- **Salvo:** `Toast`/`useToast` (`frontend/src/components/Toast.tsx`),
  provider único no `main.tsx`; confirma "X salvo" após persistir, em vez de
  save silencioso. Ligado aos saves principais: decisões, defeitos,
  afazeres, reuniões, casos de teste e requisitos.
- **Carregando:** `.spinner` e `.skeleton` canônicos no CSS (vocabulário
  único; rollout inline incremental).
- **Falhou:** toast de erro (dura mais) + classe `.field-error` para erro
  junto à ação, além do banner global do `App.tsx`.
- **Vazio:** padrão `.empty-state` reafirmado (já majoritário nas telas).
- **Dirty:** o `Modal` compartilhado ganhou `dirty?: boolean` — fechar por
  Esc/backdrop/X com o form sujo abre um `ConfirmModal` ("Descartar
  alterações?") em vez de perder o que foi digitado. Detecção de dirty via
  wrapper `.modal-form` (`display: contents`, captura `onInput` sem afetar
  layout) nos 4 modais CRUD.

### Acceptance criteria

3. [verified] — ver spec (Toast/useToast, Modal dirty, CSS, build limpo).

### Decisão

Escopo aplicado nas telas principais (6 saves + guarda em 4 modais); o
rollout do toast às telas restantes é incremental e fica registrado na skill
`estados-de-feedback-nas-telas` — coerente com como uma slice de
design-system se propaga (define o reutilizável, aplica no principal,
propaga conforme as telas são tocadas).
