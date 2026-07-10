---
name: salvar-json-truncado-de-llm
description: Quando a geração de um LLM local é cortada (timeout) no meio de um JSON grande, o objeto externo não fecha e o parse falha — perdendo TUDO. Recupere os objetos internos que já saíram inteiros em vez de retornar erro sem preview.
when: Import/geração via modelo local devolve JSON válido porém incompleto (objeto externo sem `}` final, último item cortado mid-string); a UI mostra erro/nenhum preview mesmo com o modelo tendo produzido vários itens corretos.
---

# Skill — salvar-json-truncado-de-llm

## When to use this skill

- Resposta do LLM (LM Studio/Ollama) é JSON bem-formado no começo mas **para
  no meio** — objeto externo `{ "folder":…, "testcases": [ {…}, {…}, {cortado`
  sem fechar. Log do servidor mostra "Client disconnected. Stopping generation"
  ~exatamente no valor do timeout do cliente HTTP.
- Sintoma na UI: **nenhum preview**, só erro "sem JSON" / "fora do schema",
  apesar de o modelo ter gerado N casos completos.

## Causa raiz

1. Geração de muitos itens num modelo local é lenta; o **timeout do cliente
   HTTP** corta a stream no meio. Suba o timeout (ex.: 300 s), mas ele nunca
   elimina 100% o risco de corte.
2. Um extrator que exige o **objeto externo completo** perde tudo quando ele
   não fecha — mesmo com 9 de 10 itens íntegros dentro dele. Um scanner que
   faz `i = j+1` após um `{` que não fecha **pula o corpo inteiro** e nunca vê
   os itens aninhados.

## Procedure

1. **Timeout generoso** no cliente HTTP (modelos locais levam minutos).
2. **Scanner que recupera aninhados.** Além do "objetos de nível superior",
   tenha um `_all_objects` que, ao achar `{`, tenta casar o fechamento e
   **avança só 1 char** (`i += 1`, não `i = j+1`) — assim varre também os
   objetos dentro de um externo truncado.
3. **Salvamento parcial como fallback.** Quando NENHUM objeto completo valida
   no schema-alvo, filtre os objetos aninhados que têm a "cara" do item
   (ex.: `title` + `passos`/`resultado_esperado`), valide cada um e monte o
   agregado parcial. Recupere campos do envelope (ex.: `folder`) por regex no
   cabeçalho, já que o objeto externo não fechou.
4. **Preview parcial > erro.** Devolva o que salvou; o usuário aceita os casos
   bons e reimporta o resto. Nunca troque N itens válidos por um 422.

## Anti-patterns

- Exigir JSON íntegro e falhar tudo no primeiro corte.
- Scanner de objetos que pula o corpo de um `{` não fechado (`i = j+1`).
- Confiar só no timeout maior: reduz a frequência, não elimina o corte.

## Related material

- `backend/arbites/ai.py` — `_all_objects`, `_salvage_import`,
  `complete(..., salvage=)`, `convert_import`.
- `backend/tests/test_ai_import_robustness.py`
  (`test_salvages_complete_testcases_from_truncated_output`).
- Spec `ai-assist` (#7). Relacionadas: [[modelo-de-raciocinio-content-vazio]],
  [[saida-estruturada-llm-modelo-pequeno]].
