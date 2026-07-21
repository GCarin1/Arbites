---
name: design-system-canonico
description: Gramática visual canônica do frontend Arbites (capability design-system) — as convenções fixas de botão/input/card/badge/abas/hierarquia/feedback que toda tela nova ou alterada deve seguir, em vez de estilo ad-hoc.
when: O agente vai criar ou alterar QUALQUER componente/tela do frontend (`frontend/src/**`), escolher classes CSS, montar cards/botões/abas/badges, ou revisar um diff de UI — carregue ANTES de escrever JSX/CSS.
---

# Skill — design-system-canonico

## When to use this skill

- Vai adicionar ou alterar um componente React em `frontend/src/components/`
  ou tocar em `frontend/src/styles.css`.
- Precisa decidir a classe de um botão, input, card, badge, aba, ou o
  espaçamento entre blocos.
- Está revisando um diff de frontend e quer barrar estilo ad-hoc.

A capability é `design-system` (`.doctrina/specs/design-system/spec.md`),
fundação landada nas changes 0060–0062, abas de seção na 0065. Toda tela
nova/alterada segue — sem estilo ad-hoc.

## Procedure

1. **Botões — seletor de elemento, não classe `.btn-*`.** `button` (base =
   secundário) · `button.primary` (CTA) · `button.danger` (destrutivo) ·
   `button.btn-sm` (inline pequeno). NÃO existe `.btn-primary`/
   `.btn-secondary`. No máximo **1 `primary` por bloco**.
2. **Input/select/textarea — seletor de elemento.** Altura `--h-control`,
   focus/disabled já consistentes. Não estilizar à mão.
2b. **Referência a entidade — `SingleRefInput` (busca id E título).**
   Todo campo que aponta para uma entidade existente (epic/story/CT/
   execution/defeito) usa `SingleRefInput` (de `Autocomplete.tsx`,
   `kinds="requirement|testcase|execution|defect|..."`) — nunca
   `<datalist>` casando por ID nem `<select>` cru sobre a lista de
   entidades. `<datalist>` fica RESTRITO a valores livres que não são
   entidades (ex.: squad). `<select>` fica para conjuntos fixos de valores
   (status/prioridade/tipo). Change 0082.
3. **Card — superfície compartilhada.** Fundo/borda/raio/padding (`--s2`)/
   sombra vivem numa ÚNICA regra CSS de `.card` (compartilhada por
   `.metric-card`/`.chart-card`/`.todo-card`); a variante só declara o que a
   diferencia. Não repetir a superfície nem usar `style={{ marginBottom }}`
   — usar **`.block`** (`--s3`) para o ritmo entre blocos de nível superior.
4. **Badge de status — nunca cor sozinha.** `status-dot` + classe `--dot`
   (ex.: `dot-col-failed`, `dot-active`, `dot-draft`) + **texto**. Cor nunca
   é o único indicador.
5. **Abas de seção — `.tab-bar` + `.tab-btn`.** Para separar
   trabalho/config/histórico dentro de uma página, use o padrão canônico
   (change 0065): um `<div className="tab-bar" role="tablist">` com
   `<button role="tab" aria-selected={...} className={\`tab-btn ${active ? "active" : ""}\`}>`.
   Ver `Automation.tsx` como referência. Não inventar barra de abas nova.
6. **Hierarquia e espaçamento.** Título de página `page-title`
   (`--fs-h1`/peso 700); `.subtitle` para apoio leve; espaçamento por token
   (`--s1..--s4`), nunca número mágico.
7. **Feedback (0061).** Depois de salvar, `toast("X salvo")` via `useToast`
   (provider já em `main.tsx`). Modal com edição pendente usa a guarda de
   dirty (`Modal` prop `dirty` + wrapper `.modal-form`). Carregando:
   `.spinner`/`.skeleton`; erro de campo: `.field-error`.
8. **Orientação (0062).** Ação rápida global via `CommandPalette`
   (Ctrl/Cmd+K); empty states com título + próximo passo, não só "vazio".
9. **Verificar.** Gate do frontend = `npm --prefix frontend run build`
   (tsc+vite). Não há runner de teste JS → verificação de UI = **build
   limpo + revisão visual + smoke servindo o build**.

## Anti-patterns

- Criar `.btn-primary`/`.btn-secondary` ou estilizar `<button>` inline —
  quebra a convenção de seletor de elemento e cria dois sistemas.
- Repetir a superfície do card numa nova classe, ou empurrar espaçamento com
  `style={{ marginBottom: 16 }}` em vez de `.block`.
- Cor como único sinal de status (sem `status-dot` + texto) — falha de
  acessibilidade.
- `<datalist>` casando por ID ou `<select>` cru sobre entidades para
  referenciar um card (epic/story/CT/execution/defeito) — quem não decora o
  ID não acha; use `SingleRefInput` (busca id + título).
- Montar uma barra de abas própria em vez de `.tab-bar`/`.tab-btn`.
- Mais de um `button.primary` competindo no mesmo bloco.
- Número mágico de espaçamento em vez de token `--sN`.

## Related material

- `.doctrina/specs/design-system/spec.md` — a spec da capability.
- `frontend/src/styles.css` — `.tab-bar`/`.tab-btn` (0065), `.card`/`.block`
  (0060), `status-dot`/`dot-*`, tokens `--sN`/`--h-control`/`--fs-h1`.
- `frontend/src/components/Automation.tsx` — referência viva das abas de
  seção e da separação trabalho/config.
- Memória `arbites-design-system` (mesma gramática, para recall entre
  sessões).
