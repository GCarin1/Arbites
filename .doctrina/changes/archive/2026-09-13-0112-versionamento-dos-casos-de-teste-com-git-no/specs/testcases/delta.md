# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

O workspace já era filesystem (ADR 0001). Falta a ele o que todo repositório
de código tem há trinta anos e nenhuma ferramenta de teste comercial entrega:
histórico linha a linha, comparação entre versões e volta atrás. Como o caso
de teste já é um `.md` em disco, isso não pede banco novo nem formato novo —
pede `git`, que é a tecnologia certa para exatamente este problema.

A unidade de commit é a **ação semântica** da interface, não a gravação: criar
um caso, editar, mudar de pasta e excluir viram um commit cada, com a mensagem
dizendo o que aconteceu e o autor vindo da sessão. Um commit por gravação
encheria o histórico de ruído e faria a comparação entre versões perder o
sentido.

Editar o arquivo por fora — no Obsidian, no editor favorito — continua
funcionando e também entra no histórico, como commit de autoria externa: o
arquivo é a fonte da verdade, e quem edita a fonte da verdade não deveria
precisar pedir licença.

```ops
bump-version minor
append-requirement ubiquitous: The system shall manter o workspace como repositório git, criando-o com `git init` e um `.gitignore` do índice descartável na primeira escrita quando ainda não existir `.git/`.
append-requirement ubiquitous: The system shall gravar um commit por AÇÃO semântica da interface — criar, editar, mover e excluir um caso de teste —, com mensagem descrevendo a ação e autor vindo da sessão, nunca um commit por gravação de arquivo.
append-requirement ubiquitous: The system shall expor `GET /testcases/{id}/versions` (histórico do arquivo), `GET /testcases/{id}/versions/{sha}` (o conteúdo naquele commit), `GET /testcases/{id}/versions/diff?a=&b=` (comparação unificada) e `POST /testcases/{id}/versions/{sha}/restore` (restauração).
append-requirement ubiquitous: The system shall apresentar o histórico numa aba do próprio caso de teste, com a versão escolhida comparável à atual e restaurável dali.
append-requirement event: When um arquivo do workspace é alterado por fora da interface e existe alteração não commitada, the system shall registrá-la como commit de autoria externa antes de responder o histórico, para que a edição no Obsidian não suma do registro.
append-requirement event: When uma versão anterior é restaurada, the system shall gravar a restauração como um commit NOVO, preservando o histórico em vez de reescrevê-lo.
append-requirement unwanted: The system shall not versionar o índice descartável, a lixeira nem os segredos do workspace; o que o `.gitignore` cobre não entra em commit nenhum.
append-requirement unwanted: The system shall not falhar uma operação de caso de teste porque o git falhou ou não está instalado; o versionamento é registro, e registro que derruba a escrita do usuário é pior do que registro nenhum.
append-criterion [unverified] Criar, editar e mover um caso de teste gera um commit por ação, com a mensagem da ação e o e-mail da sessão como autor, e o índice descartável fica fora do repositório — verified by `backend/tests/test_versioning.py`.
append-criterion [unverified] O histórico de um caso lista suas versões, a comparação entre duas mostra a linha alterada e restaurar uma versão anterior devolve o conteúdo gravando um commit novo — verified by `backend/tests/test_versioning.py`.
append-criterion [unverified] Uma edição feita por fora da interface entra no histórico como commit de autoria externa, e um workspace onde o git não funciona continua aceitando criar e editar casos — verified by `backend/tests/test_versioning.py`.
```
