# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

## Context

Doc de ajustes §1.1: test cases viram um repositório de pastas centralizado no
conteúdo (não no sidebar), com detalhe aberto só por clique (+ Voltar), pastas
ilimitadas (criar/excluir/drag & drop), formato **BDD (Gherkin)** como padrão do
corpo — steps do CT extraídos das linhas Given/When/Then — e data de criação
exibida.

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall aceitar corpo de CT em formato BDD (Feature/Scenario +
  Given/When/Then, EN ou PT-BR), extraindo os steps do CT das linhas Gherkin;
  este é o formato padrão de novos CTs (o formato markdown legado com
  `## Passos` permanece aceito).
- The system shall permitir criar e excluir pastas (aninhamento ilimitado) sob
  `testcases/` e mover um CT entre pastas (`POST /testcases/{id}/move`),
  preservando o ID; exclusão de pasta move o conteúdo para a lixeira.
- The system shall indexar e expor a data de criação (`created`) do CT na
  árvore e no detalhe.

### Unwanted-behavior (must-not) (ADDED)

- The system shall not emitir warning de heading ausente para corpo BDD
  válido (Scenario + steps Gherkin).
- The system shall not aceitar caminhos de pasta fora de `testcases/`
  (path traversal → 422).

## Acceptance criteria (ADDED)

5. [verified] Corpo BDD tem steps extraídos de Given/When/Then (usados no
   snapshot da execution) e não gera warning de heading — verified by
   `backend/tests/test_tc_repository.py`.
6. [verified] Criar pasta aninhada, mover CT por drag & drop (endpoint move)
   e excluir pasta (conteúdo → lixeira, fora do índice) — verified by
   `backend/tests/test_tc_repository.py`.
7. [verified] `created` indexado e presente na árvore/detalhe — verified by
   `backend/tests/test_tc_repository.py`.
