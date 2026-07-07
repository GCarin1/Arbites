# Spec Delta — capability: todos

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/todos/spec.md`

---

## Context

Refinamento de UX do M10 (M10.1): autocomplete de entidades (novo
`GET /search`) para o campo de links e para menções `@` na descrição; export
de afazeres em Markdown e XML (`GET /todos/export`, respeitando filtros ou uma
seleção); e, no frontend, filtro por período de prazo, seleção múltipla com
exclusão em massa (com confirmação "irá excluir X itens" e o botão Editar
desabilitado quando há mais de um selecionado) e descrição expansível por
linha.

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall expor `GET /search?q=&kinds=` que sugere entidades
  (CT/requisito/execução/defeito/todo) por id ou título, para autocomplete de
  links e menções.
- The system shall exportar afazeres em Markdown e XML via
  `GET /todos/export?format=`, respeitando os filtros atuais ou uma lista de
  ids selecionados.

### Event-driven (ADDED)

- When o usuário digita no campo de links ou `@` na descrição, the system
  shall sugerir entidades filtradas pelo texto digitado, navegáveis por
  teclado ou mouse.
- When o usuário seleciona vários afazeres e pede excluir, the system shall
  pedir confirmação informando a quantidade antes de excluir em massa.

### Unwanted-behavior (must-not) (ADDED)

- The system shall not habilitar a edição individual enquanto houver mais de
  um afazer selecionado.

## Acceptance criteria (ADDED)

5. [verified] `GET /search` sugere entidades por id/título, filtrável por
   kind — verified by `backend/tests/test_todos.py`.
6. [verified] Afazeres são exportáveis em Markdown e XML, respeitando
   filtros ou uma seleção de ids — verified by `backend/tests/test_todos.py`.

## Maturity (MODIFIED)

Adicionar ao **MVP (committed)**: autocomplete de links/menções (`@`),
export MD/XML, filtro por período, seleção múltipla com exclusão em massa,
descrição expansível. Remover de **Future** o "kanban arrastável" apenas se
listado; manter o restante.
