---
name: salvar-manual-feedback-e-reset-por-id
description: Botão de salvar manual sem estado de dirty/saving/saved parece "não funcionar" (salva mas nada muda na tela); e um efeito que reseta o campo a partir do valor do servidor (não do id do registro) reescreve o que o usuário digita quando há refresh de fundo.
when: Campo editável com botão "Salvar" separado (comentário, nota) num app que faz refresh periódico ou re-renderiza por outras ações; usuário relata que salvar "não faz nada".
---

# Skill — salvar-manual-feedback-e-reset-por-id

## When to use this skill

- Campo com botão "Salvar" próprio (não auto-save) e o usuário diz que o botão
  "não funciona" — mesmo a API persistindo corretamente.
- O componente tem `useEffect(() => setValor(item.campo), [item.campo, ...])`.

## Os dois problemas (foram um só relato)

1. **Sem feedback.** Salvar persiste, mas o campo já mostrava o texto digitado,
   então visualmente nada muda → parece quebrado. Verifique a API antes de
   "consertar" lógica que já funciona.
2. **Reset preso ao valor do servidor.** Um efeito que reseta o campo quando
   `item.campo` muda pode reescrever o que o usuário está digitando quando um
   refresh de fundo / outra ação re-renderiza com o valor antigo do servidor.

## Procedure

1. **Dê feedback explícito:** derive `dirty = valor !== (item.campo ?? "")`;
   botão mostra "Salvar"/"Salvando…"/"Salvo" e desabilita quando `!dirty` ou
   salvando. Assim "salvar de novo" é claramente um no-op e o estado é visível.
2. **Resete por IDENTIDADE, não por valor:** deps do efeito de reset =
   `[item.id]` (id do registro), nunca o próprio campo em edição. Trocar de
   registro reseta; refresh de fundo do mesmo registro não mexe no texto.
3. **Preserve campos correlatos ao salvar** um único campo (ex.: ao gravar só
   o comentário de um resultado, reenvie a `column` atual para não movê-lo).
4. **Verifique a camada certa:** rode a API direto (curl/script) antes de mexer
   no frontend — se a API persiste, o bug é de UX/estado, não de backend.

## Anti-patterns

- Assumir bug de backend sem testar o endpoint isolado.
- Efeito de reset com o valor editável nas deps → clobber silencioso.
- Botão de salvar sem nenhum estado visível de sucesso/dirty.

## Related material

- `frontend/src/components/Executions.tsx` — `ResultPanel` (comentário: `commentDirty`,
  `savingComment`, reset por `result.testcase_id`).
