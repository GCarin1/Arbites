# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

A capability `profile` já decidiu isto e já tem o requisito escrito: autoria
vem da sessão, nunca do corpo da requisição, "senão a autoria vira um campo
que qualquer um preenche com o nome de qualquer um". O `author_of()` existe
no `api.py` desde a change 0104, com esse comentário no corpo da função.

As rotas de resultado de execução ficaram de fora. Elas leem `who` de um
campo do payload com default `"local"`, e o efeito é duplo:

- **Autoria perdida.** Um cliente que não mande `who` — o modo guiado da
  change 0113 é exatamente esse cliente — grava `executed_by: "local"` numa
  instância multiusuário. O registro de quem executou o caso some.
- **Autoria forjável.** Um cliente que mande `who: "outra@pessoa"` atribui o
  resultado a outra pessoa, no `executed_by` e no `history[]`, que é
  justamente a trilha que deveria ser confiável.

São quatro rotas com o mesmo defeito: status do resultado, status do passo,
upload de evidência e vínculo de defeito. O campo `who` sai do contrato de
entrada das quatro; continuar aceitando-o e ignorá-lo silenciosamente seria
manter no contrato uma promessa que o servidor não cumpre.

```ops
bump-version minor
append-requirement ubiquitous: The system shall preencher a autoria de toda escrita num resultado — `executed_by` e o `who` de cada evento do `history[]` — a partir da sessão, nas rotas de status do resultado, status do passo, evidência e vínculo de defeito.
append-requirement unwanted: The system shall not aceitar `who` no corpo dessas rotas; um cliente que envie o campo recebe 422, porque ignorá-lo em silêncio deixa no contrato uma promessa que o servidor não cumpre.
append-criterion [unverified] Resultado, passo, evidência e defeito gravam como autor o e-mail da sessão, mesmo quando o corpo não traz autoria nenhuma — verified by `backend/tests/test_authorship_executions.py`.
append-criterion [unverified] Um cliente que tenta forjar a autoria de um resultado é recusado com 422 e nada é gravado, e o mesmo caso executado por duas contas registra cada resultado em nome de quem o executou — verified by `backend/tests/test_authorship_executions.py`.
```
