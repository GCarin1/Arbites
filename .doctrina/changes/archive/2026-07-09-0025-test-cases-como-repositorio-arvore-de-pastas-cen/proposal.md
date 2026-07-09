# Change 0025-test-cases-como-repositorio-arvore-de-pastas-cen — test cases como repositorio: arvore de pastas centralizada no conteudo (nao no sidebar), detalhe so por clique com botao Voltar, pastas ilimitadas (criar/excluir/drag-and-drop de CTs), formato BDD (Gherkin) como padrao do corpo com steps extraidos de Given/When/Then, data de criacao exibida

- **Status:** proposed
- **Date:** 2026-07-09
- **Owner:**
- **Affects specs:** testcases

## Why

test cases como repositorio: arvore de pastas centralizada no conteudo (nao no sidebar), detalhe so por clique com botao Voltar, pastas ilimitadas (criar/excluir/drag-and-drop de CTs), formato BDD (Gherkin) como padrao do corpo com steps extraidos de Given/When/Then, data de criacao exibida

## What

- **parser.py** — corpo BDD: `Scenario:` + linhas Given/When/Then/And/But (EN/PT)
  viram os steps do CT (`doc.is_bdd`); `check_testcase_headings` não exige mais as
  âncoras markdown quando o corpo é BDD. `## Passos` legado permanece aceito.
- **api.py** — `DEFAULT_TC_BODY` agora é o template BDD; `POST /testcases/folders`
  (criar, aninhamento ilimitado), `DELETE /testcases/folders?path=` (conteúdo →
  lixeira, reindex remove), `POST /testcases/{id}/move` (drag & drop) com guarda
  de traversal; `/tree` expõe `created`.
- **indexer.py** — coluna `created` em testcases (migração tolerante).
- **Frontend** — novo `TcRepository.tsx`: árvore de pastas **centralizada no
  conteúdo** (sidebar vira hint), expandir/colapsar, drag & drop de CTs entre
  pastas (inclusive p/ raiz), criar/excluir pasta e excluir CT com confirmação,
  data de criação por linha; detalhe abre **só por clique** com barra "← Voltar".
- **Testes** — `test_tc_repository.py` (5) + ajustes no `test_testcases.py`
  (template default agora é BDD).

## Bug encontrado no caminho (skill criada)

`DELETE /testcases/folders` registrado após `DELETE /testcases/{entity_id}` →
o path param capturava "folders" e devolvia 404. Corrigido movendo as rotas
estáticas para antes das dinâmicas (com comentário). Skill:
`rota-estatica-antes-da-dinamica`.

## Scope boundaries

- Requisitos/Execuções replicam este layout em change própria (F).
- Importação em massa via IA é change própria (G).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 98 + build do frontend).
- [x] Critérios testcases#5-7 verificados por `backend/tests/test_tc_repository.py` (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
