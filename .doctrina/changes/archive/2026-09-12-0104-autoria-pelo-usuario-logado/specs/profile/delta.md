# Spec Delta — capability: profile

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/profile/spec.md`

---

Com várias contas sobre um workspace só, `profile.md` na raiz deixa de
funcionar: ele é a memória de longo prazo injetada em toda chamada de IA, e
uma memória compartilhada faria a IA responder a um QA com o contexto de
outro. O perfil passa a ser por conta.

E a identidade logada passa a preencher a autoria, que até aqui era texto
livre — `owner` de uma execution nascia `"local"`, e requisitos, casos de
teste e defeitos não registravam autor nenhum. Numa instância de uma pessoa
isso não custava nada; numa de time, é a diferença entre a cadeia de
rastreabilidade provar algo ou não.

Escopo honesto: a autoria é **gravada no disco** (frontmatter do artefato,
`owner` da execution) e sai nas respostas que já leem o arquivo. Ela não é
indexada nem filtrável nesta entrega — quem precisa perguntar "o que fulano
mexeu" usa o log de atividade (`audit`), que já responde isso.

```ops
bump-version minor
set-header Implementation: verified — perfil por conta e autoria pela sessão (`backend/arbites/api.py`)
append-requirement ubiquitous: The system shall persistir o perfil de cada conta em `profiles/<slug-do-e-mail>.md`, com a mesma estrutura de antes (frontmatter `name`; corpo com "Preferências & Estilo" e "Contexto Ativo").
append-requirement ubiquitous: The system shall preencher a autoria a partir da sessão, e não do corpo da requisição: `owner` de uma execution e `created_by` no frontmatter de requisito, caso de teste e defeito recebem o e-mail de quem está logado.
append-requirement event: When um artefato é criado, the system shall gravar `created_by` no frontmatter dele; edições posteriores preservam o valor original, porque quem criou não muda.
append-requirement event: When uma conta lê o próprio perfil pela primeira vez e ainda não existe arquivo para ela, the system shall criá-lo a partir do template — exceto para a conta de menor id, que herda o `profile.md` da raiz uma única vez, preservando a memória escrita antes da instância virar multiusuário.
append-requirement state: While a instância roda sem autenticação (`ARBITES_AUTH=off`), the system shall continuar usando o `profile.md` da raiz e gravar autoria como `local`, para que a instalação de uma pessoa só não mude de comportamento.
append-requirement unwanted: The system shall not injetar em uma chamada de IA a memória de outra conta, nem expor o perfil de uma conta a outra por nenhuma rota.
append-requirement unwanted: The system shall not aceitar autoria vinda do corpo da requisição; um cliente que envie `owner` tem o valor ignorado, senão a autoria vira um campo que qualquer um preenche com o nome de qualquer um.
append-criterion [verified] Duas contas editam o próprio perfil e cada uma lê apenas o seu; a memória injetada no prompt de IA é a de quem chamou — verified by `backend/tests/test_authorship.py`.
append-criterion [verified] Uma execution criada por uma conta nasce com `owner` igual ao e-mail dela, mesmo que o corpo da requisição peça outro — verified by `backend/tests/test_authorship.py`.
append-criterion [verified] Requisito, caso de teste e defeito nascem com `created_by` no frontmatter, e editar o artefato depois não troca esse valor — verified by `backend/tests/test_authorship.py`.
append-criterion [verified] A conta de menor id herda o `profile.md` da raiz uma vez; a segunda conta começa do template sem enxergar a memória da primeira — verified by `backend/tests/test_authorship.py`.
append-criterion [verified] Com `ARBITES_AUTH=off` o perfil continua sendo o `profile.md` da raiz e a autoria gravada é `local` — verified by `backend/tests/test_authorship.py`.
```
