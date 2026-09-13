# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

A change 0112 acoplou commit às ações que mexem em **um** caso — criar,
editar, mover, excluir. As três ações que mexem numa pasta inteira de uma
vez ficaram de fora: excluir pasta, mover pasta e restaurar da lixeira.

O efeito é pior do que uma lacuna de registro. Reproduzido: excluir uma
pasta com dois casos deixa o repositório assim, para sempre —

```
 D testcases/regressao/CT-0001-t0.md
 D testcases/regressao/CT-0002-t1.md
```

Ninguém recolhe isso depois. A recuperação de edição externa só olha o
arquivo cujo histórico está sendo pedido, e esses casos saíram do índice —
pedir o histórico deles devolve 404. O histórico fica afirmando que os casos
existem, e a árvore de trabalho, que não. Mover uma pasta é a mesma coisa em
dobro: os caminhos antigos ficam apagados sem commit e os novos, fora do
controle de versão.

Mover e excluir pasta já são ações semânticas da interface, tão nomeáveis
quanto mover um caso. Restaurar da lixeira também: é o desfazer de uma
exclusão que foi registrada, e deixá-la de fora quebraria o par.

```ops
bump-version minor
append-requirement ubiquitous: The system shall gravar um commit também nas três ações que movem uma pasta inteira de casos de uma vez — excluir pasta, mover pasta e restaurar da lixeira —, com a mesma regra de um commit por ação e autor da sessão.
append-requirement unwanted: The system shall not deixar no repositório do workspace arquivo de caso de teste apagado ou criado por uma ação da interface sem o commit correspondente; um histórico que afirma o que a árvore de trabalho desmente não serve para comparar nem para restaurar.
append-criterion [unverified] Excluir e mover uma pasta com casos deixa um commit por ação e o repositório sem pendência, e o histórico de um caso sobrevive à mudança de pasta feita pela pasta inteira — verified by `backend/tests/test_versioning.py`.
append-criterion [unverified] Restaurar da lixeira grava o commit da volta, e o caso restaurado volta a ter histórico contínuo — verified by `backend/tests/test_versioning.py`.
```
