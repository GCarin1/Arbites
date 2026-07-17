---
name: estados-de-feedback-nas-telas
description: Toda interação que persiste, carrega ou falha precisa dos 5 estados visíveis — salvo, carregando, falhou, vazio, alterado-não-salvo — e todo empty state instrui o próximo passo; salvar em silêncio corrói a confiança do usuário.
when: O agente vai implementar ou revisar uma tela/fluxo do frontend que salva dados, carrega dados assíncronos, pode falhar ou pode estar vazio (praticamente qualquer feature de UI).
---

# Skill — estados-de-feedback-nas-telas

## When to use this skill

- O agente vai adicionar um formulário, modal ou ação de salvar.
- O agente vai renderizar uma lista/painel que carrega de API e pode vir
  vazio.
- O agente está revisando um fluxo onde o save/erro acontece "em silêncio".

## Procedure

Para cada fluxo novo, percorra o checklist dos 5 estados:

1. **Salvo** — confirmação visível e transitória após persistir (toast ou
   "salvo ✓" inline). Fechar o modal sem nenhum sinal NÃO é confirmação.
2. **Carregando** — indicador consistente (o canônico da app; não inventar
   um "Carregando..." novo por tela). Desabilitar o botão enquanto envia
   (`disabled={saving}` — padrão já usado nos modais).
3. **Falhou** — erro PERTO da ação que falhou, com mensagem acionável; o
   banner global do `App.tsx` é fallback, não o canal primário.
4. **Vazio** — sempre `.empty-state` com título + instrução do próximo
   passo ("configure X em Y para ver dados aqui"), nunca um espaço em
   branco ou um `<p>vazio</p>` seco.
5. **Dirty** — formulário/modal com alteração pendente sinaliza e pede
   confirmação ao descartar (fechar modal com texto digitado não pode
   perder o trabalho em silêncio).

Textos de apoio: se a interface já se explica, corte o parágrafo — 1 linha
de apoio + tooltip no ponto certo. Bloco longo de explicação é sinal de que
a UI precisa melhorar, não o texto crescer.

## Anti-patterns

- Salvar sem feedback: o usuário clica de novo (duplica) ou sai sem saber
  se persistiu.
- Erro só no banner global do topo enquanto o usuário olha para o modal lá
  embaixo — ele não vê e acha que o botão não funcionou.
- Empty state que só constata ("Nenhum item") sem dizer como sair dele.
- Fechar modal dirty descartando silenciosamente o que foi digitado.
- Parágrafos de ajuda repetindo o que os labels já dizem.

## Implementação canônica (landou na 0061)

- **Salvo:** `useToast().toast("X salvo")` após o `await api.save…` — antes
  do `onSaved()`. Provider único em `main.tsx` (`ToastProvider`).
- **Dirty:** passar `dirty={dirty && !saving}` ao `Modal` compartilhado —
  ele já pede confirmação ao fechar por Esc/backdrop/X. Detecção sem tocar
  cada setter: envolver os campos num `<div className="modal-form"
  onInput={() => setDirty(true)}>` — a classe é `display: contents`, então
  captura os eventos por bubbling sem gerar caixa (zero impacto no layout) e
  o `setBody` programático do load assíncrono NÃO dispara (evita falso
  dirty).
- **Carregando/erro:** `.spinner`/`.skeleton`/`.field-error` no CSS.

## Related material

- `frontend/src/components/Toast.tsx` · `frontend/src/components/Modal.tsx`
  (prop `dirty`) · `frontend/src/styles.css` (`.toast`/`.spinner`/
  `.field-error`/`.modal-form`).
- `.doctrina/specs/design-system/spec.md` — critério #3 (estados).
- [[salvar-inclui-formulario-pendente]] · [[modais-aninhados-esc-fecha-so-o-do-topo]]
  — lições de modal/salvamento já capturadas.
- [[gramatica-de-componentes-canonicos]] — a slice irmã (fundação).
