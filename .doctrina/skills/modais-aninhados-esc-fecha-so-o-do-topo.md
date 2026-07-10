---
name: modais-aninhados-esc-fecha-so-o-do-topo
description: Um componente Modal com listener de Esc no document fecha TODOS os modais abertos simultaneamente quando dois são aninhados, não só o do topo — porque stopPropagation() não impede outros listeners registrados no mesmo alvo (document). Precisa de uma pilha de modais abertos.
when: Ao abrir um Modal de dentro de outro Modal (ex.: "criar X" a partir de um formulário que já está num modal) pela primeira vez num componente Modal compartilhado que nunca precisou lidar com aninhamento antes.
---

# Skill — modais-aninhados-esc-fecha-so-o-do-topo

## When to use this skill

- Vai renderizar um `<Modal>` de dentro do `children`/fluxo de outro `<Modal>`
  já aberto (ex.: "Criar defeito" acionado de dentro do modal de edição de um
  resultado de execução).
- Sintoma se não tratado: apertar Esc no modal interno fecha os DOIS modais
  de uma vez, em vez de só o de cima.

## Causa raiz

`stopPropagation()` impede que um evento **suba** para listeners em
ancestrais do alvo — não impede que **outros listeners registrados no MESMO
alvo** também disparem. Se cada `Modal` registra seu próprio
`document.addEventListener("keydown", onKey)`, e dois modais estão montados
ao mesmo tempo, **os dois listeners disparam** no mesmo Esc, cada um chamando
seu próprio `onClose`. `stopPropagation()` não muda isso porque não há
travessia de árvore envolvida — ambos os listeners estão no `document`.

## Procedure

1. Mantenha uma pilha module-level (`openModalIds: number[]`) do componente
   `Modal` compartilhado.
2. Cada instância recebe um id estável (`useRef(++modalIdSeq).current`),
   empilha no mount (`useEffect` com push) e desempilha no unmount.
3. O handler de Esc só age se o próprio id for o **topo da pilha**:
   `if (e.key === "Escape" && openModalIds.at(-1) === modalId) onClose()`.
4. Cliques no backdrop já são naturalmente corretos (o handler só dispara
   quando `e.target === e.currentTarget`, escopado ao overlay daquele modal
   específico) — só o Esc via `document` precisa da pilha.

## Anti-patterns

- Confiar em `stopPropagation()`/`stopImmediatePropagation()` sem entender
  que múltiplos listeners no MESMO nó (não em ancestrais) não têm relação de
  bubbling entre si — `stopPropagation` não os afeta.
- Só perceber o bug quando o usuário aninha modais pela primeira vez em
  produção — teste explicitamente "abrir modal B de dentro do modal A, Esc"
  ao introduzir o primeiro caso de aninhamento no código.

## Related material

- `frontend/src/components/Modal.tsx` — `openModalIds`, `modalId`.
- `frontend/src/components/Executions.tsx` — primeiro caso real de
  aninhamento (`NewDefectModal` dentro do modal de `ResultPanel`).
