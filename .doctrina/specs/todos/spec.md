# Spec — todos

**Capability:** todos
**Status:** active
**Implementation:** verified — M10 + M10.1 (busca/autocomplete, export MD/XML, seleção múltipla, descrição com menções); backend/arbites/api.py, backend/arbites/indexer.py, backend/arbites/workspace.py; frontend Todos.tsx, Autocomplete.tsx. ID `TD-`, arquivos em `todos/`
**Realizes:** SC11
**Last updated:** 2026-07-06
**Version:** 0.4.0

## Purpose

Uma aba de afazeres local para o QA planejar e rastrear o próprio trabalho.
Cada todo é um `.md` em `todos/` (fonte de verdade no disco, versionável por
git, editável no Obsidian), com data, status e links para os artefatos que
já existem (CT/execução/story). É a base que a Daily (M11) digere para
gerar o resumo do dia; por isso "impedimento" é um status de primeira
classe. Sem IA, a aba é 100% funcional (planejamento manual); a digestão
por IA é M11.

## Requirements (EARS)

### Ubiquitous

- The system shall representar cada todo como `.md` em `todos/` com
  frontmatter `id`, `title`, `status (open|doing|blocked|done)`, `due`
  (data, opcional), `squad` (opcional), `links` (lista de IDs de
  CT/execução/story/requisito) e `created`.
- The system shall expor CRUD `GET /todos`, `POST /todos`,
  `PUT /todos/{id}`, `DELETE /todos/{id}`.
- The system shall indexar todos (status, due, squad, links) para listagem
  e filtros O(1).
- The system shall resolver os títulos dos artefatos linkados (CT/execução/
  story) para exibição, a partir dos IDs.
- The system shall expor `GET /search?q=&kinds=` que sugere entidades
  (CT/requisito/execução/defeito/todo) por id ou título, para autocomplete de
  links e menções.
- The system shall exportar afazeres em Markdown e XML via
  `GET /todos/export?format=`, respeitando os filtros atuais ou uma lista de
  ids selecionados.
- The system shall oferecer listas de To Do como artefato proprio do workspace, cada uma com titulo, prazo da lista, estado e linhas verificaveis, mantendo o arquivo legivel e editavel por uma pessoa.
- The system shall permitir vincular uma linha de lista a um afazer, gravando o vinculo apenas na linha e expondo o sentido inverso como consulta, para que os dois lados nunca possam se contradizer.
- The system shall apresentar o afazer com a cor do seu estado na borda inteira do cartao, para que a mudanca de estado seja vista.

### Event-driven

- When o usuário filtra por status ou por período (`due`), the system shall
  listar apenas o subconjunto correspondente.
- When o usuário digita no campo de links ou `@` na descrição, the system
  shall sugerir entidades filtradas pelo texto digitado, navegáveis por
  teclado ou mouse.
- When o usuário seleciona vários afazeres e pede excluir, the system shall
  pedir confirmação informando a quantidade antes de excluir em massa.
- When uma lista com prazo tem linha em aberto e o prazo chega ou passa, the system shall anuncia-la no sino informando quantas linhas restam.

### State-driven

- While um todo está `blocked`, the system shall destacá-lo como
  impedimento (insumo direto da Daily em M11).

### Unwanted-behavior (must-not)

- The system shall not exigir `due`, `squad` ou `links` (todos opcionais);
  um todo mínimo é `title` + `status`.
- The system shall not descartar todos concluídos: `done` permanece
  consultável por data (histórico).
- The system shall not habilitar a edição individual enquanto houver mais de
  um afazer selecionado.
- The system shall not aceitar o mesmo afazer vinculado a mais de uma linha, recusando com o motivo, porque a pergunta sobre a conclusao dele passaria a depender de varias linhas.

### Optional

- Where um `link` aponta para um ID inexistente no índice, the system may
  registrar um warning de integridade (mesma esteira dos warnings atuais).

## Acceptance criteria

1. [verified] CRUD de todo com status/due/squad/links persistido em
   `todos/*.md` e refletido no índice — verified by `backend/tests/test_todos.py`.
2. [verified] Filtrar todos por status e por período (`due`) retorna o
   subconjunto correto — verified by `backend/tests/test_todos.py`.
3. [verified] Todos `done` permanecem consultáveis por data (histórico não
   se perde) — verified by `backend/tests/test_todos.py`.
4. [verified] Links para CT/execução/story resolvem o título do artefato
   para exibição — verified by `backend/tests/test_todos.py`.
5. [verified] `GET /search` sugere entidades por id/título, filtrável por
   kind — verified by `backend/tests/test_todos.py`.
6. [verified] Afazeres são exportáveis em Markdown e XML, respeitando
   filtros ou uma seleção de ids — verified by `backend/tests/test_todos.py`.
7. [unverified] Lista vira arquivo com id proprio e linhas; id de linha nunca e reaproveitado; um afazer se vincula a uma linha so e a recusa nomeia a lista ocupada; o afazer sabe de que linha participa sem guardar o vinculo duas vezes; lista com prazo e linha aberta aparece no sino — verified by `backend/tests/test_listas_todo.py`.

## Maturity

**MVP (committed):**

- CRUD, `due`, `links` para CT/execução/story, status incl. `blocked`
  (impedimento), filtro por status/período, histórico consultável,
  autocomplete de links/menções (`@`), export MD/XML, seleção múltipla com
  exclusão em massa, descrição expansível.

**Future (aspirational, not committed):**

- Recorrência de todos; kanban de status arrastável; agrupamento por squad;
  ação da Daily criando todos a partir de action items (M11).

## Out of scope for this spec

- Digestão por IA / geração da daily (é M11 — capability `daily`).
- Virar um gerenciador de projetos completo (dependências, gantt, esforço).
