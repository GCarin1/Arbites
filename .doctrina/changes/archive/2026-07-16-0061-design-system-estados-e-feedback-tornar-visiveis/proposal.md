# Change 0061-design-system-estados-e-feedback-tornar-visiveis — Design system - estados e feedback: tornar visiveis e consistentes os estados salvo/carregando/falhou/vazio/alterado-nao-salvo (dirty) em toda a app. Empty states com instrucao util. Reduzir textos longos: ajuda curta e contextual (uma linha de apoio, link ver-exemplo, tooltip no ponto certo) onde a interface ja e autoexplicativa.

- **Status:** applied
- **Applied:** 2026-07-16
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** design-system

## Why

Design system - estados e feedback: tornar visiveis e consistentes os estados salvo/carregando/falhou/vazio/alterado-nao-salvo (dirty) em toda a app. Empty states com instrucao util. Reduzir textos longos: ajuda curta e contextual (uma linha de apoio, link ver-exemplo, tooltip no ponto certo) onde a interface ja e autoexplicativa.

## What

2ª slice do design-system (depende da fundação 0060). Cria a linguagem
única de FEEDBACK DE ESTADO e a aplica nas telas:

- **Salvo**: confirmação visível e transitória (toast/inline "salvo ✓") após
  qualquer persistência — hoje o salvar é silencioso na maioria das telas.
- **Carregando**: indicador consistente (spinner/skeleton) — hoje há textos
  "Carregando…" ad-hoc por tela, cada um de um jeito.
- **Falhou**: erro perto da ação que falhou (não só o banner global do
  `App.tsx`), com mensagem acionável.
- **Vazio**: revisar todos os empty states para o padrão `.empty-state` com
  instrução útil ("o que fazer para deixar de estar vazio") — algumas telas
  têm, outras só um `<p className="empty">`.
- **Dirty (alterado-não-salvo)**: sinal visual em formulários/modais com
  alterações pendentes + confirmação ao fechar sem salvar.
- **Clareza de texto**: reduzir explicações longas onde a UI é
  autoexplicativa; padrão de ajuda = 1 linha de apoio + tooltip no ponto
  certo (componente/classe de tooltip canônico).

Artefatos prováveis: componente `Toast`/`useToast`, classe de skeleton,
padrão `.field-error`, hook `useDirty` para modais, revisão de textos.

## Scope boundaries

Não muda a gramática de componentes (0060) nem navegação/orientação (0062).
Não adiciona validação de formulário nova — só torna visível o que já
acontece (salvar/carregar/falhar). Não traduz nem reescreve TODOS os textos;
só os que a tela já explica sozinha.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
