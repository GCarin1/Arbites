# Spec Delta — capability: audit

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/audit/spec.md`

---

A `audit` até aqui respondia "como está a saúde do projeto". Com vários
usuários sobre o mesmo workspace ela ganha uma segunda pergunta, de outra
natureza: **quem fez o quê e quando.** As duas convivem — a auditoria de
qualidade continua sendo um retrato sob demanda; o log de atividade é
contínuo e nunca é recalculado.

A decisão de forma que sustenta o resto: o registro é feito **no gate**,
depois da resposta, para toda escrita bem-sucedida — e não anotando rota a
rota. Uma rota de escrita nova entra no log sozinha. O preço é que a entrada
descreve a requisição (método, caminho, status) em vez da intenção de
negócio, e é um preço que vale: uma lista mantida à mão fica desatualizada
exatamente nas rotas que alguém acrescentou às pressas.

O log vive no banco durável das contas (ADR 0011), não no índice
descartável: um `reindex` não pode apagar a prova de quem apagou o quê.

```ops
bump-version minor
set-header Implementation: verified — snapshot de qualidade (`backend/arbites/audit.py`) + log de atividade no gate (`backend/arbites/api.py`, `backend/arbites/auth.py`)
append-requirement ubiquitous: The system shall registrar em `.arbites/auth.db` toda requisição de escrita bem-sucedida sob o prefixo da API — data, id e e-mail do autor, método, caminho, código de resposta e IP real — sem depender de anotação rota a rota, de modo que uma rota de escrita nova seja registrada sozinha.
append-requirement ubiquitous: The system shall expor `GET /admin/activity` (apenas `admin`), mais recente primeiro, paginado por `limit` e `offset`, filtrável por autor (`user`), por trecho de caminho (`path`) e por intervalo de datas (`from`, `to`).
append-requirement ubiquitous: The system shall manter o log de atividade separado das rodadas de auditoria de qualidade: aquele é contínuo e imutável, estas são retratos sob demanda.
append-requirement event: When uma requisição de escrita falha (resposta 4xx ou 5xx), the system shall deixá-la fora do log de atividade — tentativa recusada não é ação; as de autenticação já vivem no registro de acessos.
append-requirement unwanted: The system shall not gravar corpo de requisição no log de atividade; caminho e método bastam para responder quem mexeu no quê, e o corpo carregaria senha, token e conteúdo de artefato para dentro de um registro que ninguém apaga.
append-requirement unwanted: The system shall not oferecer rota de exclusão ou edição de entrada do log de atividade; um registro que o próprio suspeito pode apagar não prova nada.
append-criterion [verified] Criar, editar e apagar um caso de teste deixa três entradas no log com o e-mail de quem fez, método, caminho e IP, na ordem inversa da execução — verified by `backend/tests/test_activity_log.py`.
append-criterion [verified] Uma escrita recusada por papel ou por interruptor não entra no log, e uma leitura por GET também não — verified by `backend/tests/test_activity_log.py`.
append-criterion [verified] O log filtra por autor, por trecho de caminho e por intervalo de datas, e pagina — verified by `backend/tests/test_activity_log.py`.
append-criterion [verified] Nenhuma entrada do log carrega corpo de requisição, e não existe rota que apague ou edite o log; reindexar o workspace não o afeta — verified by `backend/tests/test_activity_log.py`.
```
