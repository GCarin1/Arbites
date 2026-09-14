# Spec Delta — capability: todos

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/todos/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer listas de To Do como artefato proprio do workspace, cada uma com titulo, prazo da lista, estado e linhas verificaveis, mantendo o arquivo legivel e editavel por uma pessoa.
append-requirement ubiquitous: The system shall permitir vincular uma linha de lista a um afazer, gravando o vinculo apenas na linha e expondo o sentido inverso como consulta, para que os dois lados nunca possam se contradizer.
append-requirement unwanted: The system shall not aceitar o mesmo afazer vinculado a mais de uma linha, recusando com o motivo, porque a pergunta sobre a conclusao dele passaria a depender de varias linhas.
append-requirement event: When uma lista com prazo tem linha em aberto e o prazo chega ou passa, the system shall anuncia-la no sino informando quantas linhas restam.
append-requirement ubiquitous: The system shall apresentar o afazer com a cor do seu estado na borda inteira do cartao, para que a mudanca de estado seja vista.
append-criterion [unverified] Lista vira arquivo com id proprio e linhas; id de linha nunca e reaproveitado; um afazer se vincula a uma linha so e a recusa nomeia a lista ocupada; o afazer sabe de que linha participa sem guardar o vinculo duas vezes; lista com prazo e linha aberta aparece no sino — verified by `backend/tests/test_listas_todo.py`.
bump-version minor
```
