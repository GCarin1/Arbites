---
name: salvar-inclui-formulario-pendente
description: Formulário com "Adicionar à lista" + "Salvar" separados perde dados — o Salvar deve incluir o item pendente do formulário, senão o usuário preenche e nada persiste.
when: Ao construir/editar UI onde há um formulário para adicionar um item a uma lista e um botão de salvar separado (config de providers, tags, membros, targets…).
---

# Skill — salvar-inclui-formulario-pendente

## When to use this skill

- A tela tem um formulário ("adicionar X") que empurra para uma lista local,
  e um botão "Salvar" que persiste a lista.
- Um bug relata "preenchi os dados e cliquei em salvar, mas não salvou nada".

## O bug (real, config de IA)

O card de Providers tinha o formulário (nome/kind/modelo/base_url/chave) e uma
lista. "Adicionar à lista" empurrava o formulário para a lista; "Salvar
configuração" só persistia **a lista**. Quem preenchia o formulário e clicava
direto em Salvar (fluxo natural) via nada acontecer — o item pendente nunca
entrava no payload.

## Procedure

1. No handler de salvar, **inclua o formulário pendente** antes de montar o
   payload (sem exigir o clique em "Adicionar"):
   ```tsx
   let eff = list;
   if (form.name.trim()) {
     const pending = {...form};
     eff = [...list.filter(x => x.name !== pending.name), pending];
     // idem para chaves/secret e default associados
   }
   await api.save({ items: eff, ... });
   // limpe os campos do formulário após sucesso
   ```
2. Mantenha "Adicionar à lista" como atalho opcional (para adicionar vários
   antes de salvar), mas nunca o torne obrigatório para persistir.
3. Deixe claro na UI: uma legenda "preencha acima e salve — incluído
   automaticamente".
4. Teste o fluxo do usuário comum: preencher → Salvar (sem Adicionar) → recarregar
   → o item persiste.

## Anti-patterns

- Estado do formulário desacoplado do payload de salvar, sem reconciliar.
- Confiar que o usuário vai clicar no botão intermediário ("Adicionar")
  antes de Salvar.

## Related material

- `frontend/src/components/AiAssist.tsx` — `ProvidersCard.save()`.
