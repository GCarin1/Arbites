# Spec — decisions

**Capability:** decisions
**Status:** active
**Implementation:** verified — M14 (backend/arbites/indexer.py, backend/arbites/api.py, frontend/src/components/Decisions.tsx)
**Realizes:** n/a — capability nova (Memória Histórica do Projeto), fora do escopo do intake original; surgiu de uma sessão de brainstorm sobre memória/contexto para IA
**Last updated:** 2026-07-11
**Version:** 0.1.1

## Purpose

Registra **decisões arquiteturais do time de QA sobre o projeto sob teste**
— não o sistema de ADR do próprio framework Doctrina (`.doctrina/decisions/`,
que é meta e nunca é tocado por esta capability). É o segundo pilar da
"Memória Histórica do Projeto" (o primeiro é lição aprendida em `defects`):
meses depois, o time — e a IA, via `/search` e menções `@DEC-XXXX` — ainda
sabe por que uma decisão foi tomada. Mesmo espírito de `defects`: ponteiro +
metadados, sem tentar ser um sistema de governança completo.

## Requirements (EARS)

### Ubiquitous

- The system shall representar decisão como `.md` em `decisions/` com
  frontmatter `id`, `title`, `status (proposed|accepted|superseded)`,
  `squad`, `tags`, `supersedes` (id de outra decisão, opcional), `created`.
- The system shall expor `GET /decisions` (filtros `status`, `squad`),
  `GET /decisions/{id}` (com corpo), `POST /decisions`, `PUT /decisions/{id}`,
  `DELETE /decisions/{id}` (lixeira).
- The system shall oferecer um corpo padrão ao criar sem `body` explícito,
  com as seções "Contexto", "Decisão" e "Consequências".
- The system shall expor uma aba dedicada ("Decisões") com listagem,
  filtro por status, criação, edição e exclusão.
- The system shall indexar decisões para autocomplete/menção (`GET /search`,
  `kind: "decision"`) e para resolução de links em Afazeres, no mesmo
  mecanismo já usado por CT/requisito/execução/defeito.

### Event-driven

- When o usuário navega por uma menção/link `@DEC-XXXX`, the system shall
  abrir a aba Decisões com o editor daquela decisão já aberto.

### Unwanted-behavior (must-not)

- The system shall not confundir/mesclar este artefato com o sistema de ADR
  do próprio Doctrina (`.doctrina/decisions/`); são namespaces e propósitos
  totalmente separados.
- The system shall not tentar ser um sistema de governança de decisões
  completo (sem workflow de aprovação/revisão) — é ponteiro + metadados,
  mesmo princípio de `defects`.

### Optional

- Where `supersedes` aponta para outra decisão, the system may exibir esse
  vínculo como referência navegável.

## Acceptance criteria

1. [verified] Criar uma decisão sem `body` grava o template padrão
   (Contexto/Decisão/Consequências); com `body` explícito, grava o
   informado — verified by `backend/tests/test_decisions.py`.
2. [verified] Listar filtra por `status` e por `squad`; `GET/PUT/DELETE
   /decisions/{id}` funcionam (edição parcial preserva campos não
   enviados; exclusão vai para a lixeira, não apaga) — verified by
   `backend/tests/test_decisions.py`.
3. [verified] Uma decisão aparece em `GET /search` com `kind: "decision"` e
   sobrevive a um reindex completo — verified by
   `backend/tests/test_decisions.py`.

4. [verified] A aba exibe subtitle de propósito e o empty state traz um
   exemplo concreto (genérico) de decisão — verified by build + revisão
   visual (`frontend/src/components/Decisions.tsx`).

## Maturity

**MVP (committed):**

- CRUD completo, filtro por status/squad, template de corpo, busca/menção
  (`@DEC-XXXX`), aba dedicada na UI.

**Future (aspirational, not committed):**

- Interface de "conversa" com a Memória Histórica (chat sobre
  decisões/lições/defeitos) — hoje a memória é browsable/buscável e
  consumível por agentes externos via Context Pack (capability separada),
  não um chat dentro do Arbites.
- Vínculo formal decisão → requisito/CT afetado (hoje é só menção livre no
  corpo).

## Out of scope for this spec

- O sistema de ADR do próprio framework Doctrina (`.doctrina/decisions/`).
- Lição aprendida de defeitos (ver `defects`).
- Export/Context Pack para agentes de IA externos (capability separada).
