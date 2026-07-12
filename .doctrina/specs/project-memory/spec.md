# Spec — project-memory

**Capability:** project-memory
**Status:** active
**Implementation:** verified
**Realizes:** n/a — capability nova (Memória Histórica do Projeto e para a IA), fora do escopo do intake original; surgiu de uma sessão de brainstorm sobre memória/contexto para IA
**Last updated:** 2026-07-12
**Version:** 0.1.0

## Purpose

A maioria dos projetos perde conhecimento: decisões, causas de bugs e o
histórico de por que algo foi feito de um jeito ficam espalhados ou se
perdem. Esta capability dá ao projeto (e à IA) uma linha do tempo única,
cronológica, estilo `git log` — mas conversacional — que cruza requisitos,
defeitos, lições aprendidas, decisões arquiteturais e interações de agentes
de IA. Ela também alimenta as próprias chamadas de IA que geram conteúdo
com um recap do que já aconteceu no projeto: a IA fica mais inteligente
conforme o projeto cresce, não presa a um contexto fixo.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /memory/timeline?kinds=&limit=` que devolve
  uma lista de eventos ordenados do mais recente para o mais antigo,
  cruzando 5 tipos: `requirement` (requisito criado), `defect` (defeito
  aberto), `lesson` (defeito com causa raiz registrada — ver capability
  `defects`), `decision` (decisão arquitetural registrada — ver capability
  `decisions`) e `agent` (interação de IA que gerou conteúdo).
- The system shall registrar um evento `agent` (persistido em
  `agent_log/AGT-NNNN.md`, com frontmatter `at`/`action`/`target_id`/
  `target_title` e o corpo como resumo humano) toda vez que
  `generate-testcases`, `review` ou `negative-cases` completa com sucesso.
- The system shall aceitar o filtro `kinds` (lista separada por vírgula,
  subconjunto de `requirement,defect,lesson,decision,agent`) e `limit`
  (default 50, máx. 200) em `GET /memory/timeline`.
- The system shall injetar, nas chamadas de IA `generate-testcases` e
  `review`, um recap textual das últimas decisões aceitas e das últimas
  lições aprendidas do projeto — além (não em substituição) da injeção de
  lições por similaridade textual já existente
  (`ai.find_relevant_lessons`).

### Event-driven

- When um defeito tem `root_cause` preenchido, the system shall também
  emitir um evento `lesson` na timeline (com o mesmo `at` do defeito),
  além do evento `defect` — os dois convivem, não é um substituindo o
  outro.
- When nenhuma decisão aceita ou lição existe no workspace, the system
  shall injetar o texto original sem nenhum bloco de recap (prompt limpo,
  sem seção vazia).

### Unwanted-behavior (must-not)

- The system shall not persistir o log de interações de agentes apenas no
  índice SQLite — como todo o resto do Arbites (ADR 0001), o filesystem
  (`agent_log/`) é a fonte de verdade e o índice é reconstruível via
  reindex.
- The system shall not referenciar nenhuma empresa/organização/projeto
  específico nesta capability.

### Optional

- Where o usuário filtra por um subconjunto de `kinds`, the system may
  omitir os demais tipos da resposta sem alterar a ordenação relativa dos
  tipos incluídos.

## Acceptance criteria

1. [verified] `GET /memory/timeline` cruza requisitos, defeitos, decisões
   e eventos de agente num único feed ordenado do mais recente pro mais
   antigo — verified by `backend/tests/test_project_memory.py`.
2. [verified] Um defeito com `root_cause` preenchido gera um evento
   `lesson` distinto do evento `defect`; sem `root_cause`, só o evento
   `defect` aparece — verified by `backend/tests/test_project_memory.py`.
3. [verified] O filtro `kinds` restringe a resposta ao(s) tipo(s) pedido(s);
   `limit` corta o total de eventos devolvidos — verified by
   `backend/tests/test_project_memory.py`.
4. [verified] `generate-testcases`, `review` e `negative-cases` registram
   um evento `agent` na timeline após completar — verified by
   `backend/tests/test_project_memory.py`.
5. [verified] `generate-testcases` e `review` recebem, no prompt enviado ao
   provider de IA, um recap com as decisões aceitas e lições recentes do
   projeto quando existem; o recap fica ausente quando não há nenhuma —
   verified by `backend/tests/test_project_memory.py`.
6. [verified] Eventos de agente sobrevivem a `reindex` (persistidos como
   Markdown em `agent_log/`, não só no índice) — verified by
   `backend/tests/test_project_memory.py`.

## Maturity

**MVP (committed):**

- Linha do tempo cruzando requisito/defeito/lição/decisão/agente, filtro
  por tipo e limite, log de interações de agentes de IA que geram
  conteúdo, recap de decisões+lições injetado em generate-testcases e
  review, nova aba "Memória do Projeto" no menu.

**Future (aspirational, not committed):**

- Busca textual dentro da timeline.
- Paginação (hoje é só `limit`, sem cursor/offset).
- Registrar também `daily digest` e resumo de reunião como eventos de
  agente (hoje ficam de fora — já têm tela própria).

## Out of scope for this spec

- Edição/curadoria manual dos eventos da timeline — ela é 100% derivada,
  não editável.
- Substituir a memória de longo prazo do Perfil (`_with_memory`) — o recap
  desta capability é automático e derivado dos dados, a memória do Perfil é
  manual e curada pelo usuário; as duas convivem, empilhadas no mesmo
  prompt.
