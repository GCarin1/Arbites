# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

O histórico de um caso é lido com `--follow`, de propósito: mover um caso
preserva o ID, e deveria preservar o passado. Ele funciona — a lista mostra
as versões anteriores à mudança de pasta.

Abrir ou restaurar qualquer uma delas, não. Ver o conteúdo, comparar e
restaurar pedem o arquivo ao git pelo caminho de **hoje**, e naquele commit
o arquivo estava em outro lugar. O git responde que não existe, e a rota
devolve 404.

O resultado é uma tela que oferece o que não entrega: a versão aparece
listada, com autor e data, e os botões de comparar e restaurar falham. Um
histórico que não permite voltar é um histórico pela metade — foi
exatamente isso que a change 0112 se propôs a resolver.

O git sabe onde o arquivo estava em cada commit; é a mesma travessia que o
`--follow` já faz para montar a lista. Basta perguntar.

```ops
bump-version patch
append-requirement ubiquitous: The system shall resolver, para cada versão de um caso de teste, o caminho que o arquivo tinha naquele commit, de modo que ver, comparar e restaurar funcionem também nas versões anteriores a uma mudança de pasta.
append-criterion [unverified] Uma versão anterior à mudança de pasta é aberta, comparada e restaurada pelo ID do caso, sem depender de onde o arquivo está hoje — verified by `backend/tests/test_versioning.py`.
```
