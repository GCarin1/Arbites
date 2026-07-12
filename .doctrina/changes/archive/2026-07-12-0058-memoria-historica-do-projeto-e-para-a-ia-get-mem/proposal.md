# Change 0058-memoria-historica-do-projeto-e-para-a-ia-get-mem — Memoria Historica do Projeto e para a IA: GET /memory/timeline cruza requisitos, defeitos, licoes aprendidas (defeitos com root_cause), decisoes arquiteturais e interacoes de agentes de IA (novo: agent_events, persistido em agent_log/) numa linha do tempo cronologica estilo git log, filtravel por tipo (kinds=) e limitavel. Cada chamada de IA que gera conteudo (generate-testcases, review-testcase, negative-cases) registra um evento no log de agentes. Alem da tela, decisoes aceitas + licoes recentes sao injetadas como recap no prompt de generate-testcases e review (_with_project_recap), complementando a injecao de licoes por similaridade que ja existia (find_relevant_lessons) - a IA fica mais inteligente conforme o projeto cresce. Nova aba 'Memoria do Projeto' no menu.

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** project-memory

## Why

Memoria Historica do Projeto e para a IA: GET /memory/timeline cruza requisitos, defeitos, licoes aprendidas (defeitos com root_cause), decisoes arquiteturais e interacoes de agentes de IA (novo: agent_events, persistido em agent_log/) numa linha do tempo cronologica estilo git log, filtravel por tipo (kinds=) e limitavel. Cada chamada de IA que gera conteudo (generate-testcases, review-testcase, negative-cases) registra um evento no log de agentes. Alem da tela, decisoes aceitas + licoes recentes sao injetadas como recap no prompt de generate-testcases e review (_with_project_recap), complementando a injecao de licoes por similaridade que ja existia (find_relevant_lessons) - a IA fica mais inteligente conforme o projeto cresce. Nova aba 'Memoria do Projeto' no menu.

## What

Nova capability `project-memory`. Backend: `backend/arbites/project_memory.py`
(`timeline()`/`recent_recap()`), nova tabela `agent_events` + SUBDIR
`agent_log/` + prefixo `AGT` (`indexer.py`/`workspace.py`), helpers
`_log_agent_event`/`_with_project_recap` em `api.py` (wireados em
`ai_generate`/`ai_review`/`ai_negative`), endpoint `GET /memory/timeline`.
Frontend: `Memory.tsx` (linha do tempo estilo git log, filtro por tipo),
tipos em `types.ts`, client `memoryTimeline()` em `api.ts`, nova aba
"Memória do Projeto" em `App.tsx`, CSS `.memory-*` em `styles.css`.

## Scope boundaries

Não registra `daily digest` nem resumo de reunião como eventos de agente
(escopo confirmado com o usuário: só chamadas que geram/alteram conteúdo de
QA — generate-testcases/review/negative-cases). O recap de decisões+lições
só é injetado em generate-testcases e review (negative-cases mantém só a
memória de longo prazo do Perfil, sem recap). A timeline é 100% derivada —
sem edição manual de eventos.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
