# Spec — requirements

**Capability:** requirements
**Status:** active
**Implementation:** verified — M0 (backend/arbites/api.py, backend/arbites/indexer.py)
**Realizes:** SC1
**Last updated:** 2026-07-20
**Version:** 0.7.0

## Purpose

Gerencia requisitos locais — Epics e Stories — como arquivos Markdown com
frontmatter em `requirements/`. A story local é um espelho resumido do
detalhe que vive no Confluence (colagem manual na v1), com `external_key`
apontando para o sistema corporativo (Jira hoje, Businessmap depois).

## Requirements (EARS)

### Ubiquitous

- The system shall representar Epic como `.md` com frontmatter `id`,
  `kind: epic`, `title`, `status (active|done|cancelled)`, `external_key`,
  `tags`.
- The system shall representar Story como `.md` com frontmatter `id`,
  `kind: story`, `title`, `epic`, `status`, `external_key`,
  `confluence_url` (opcional), `tags`.
- The system shall expor CRUD via `GET/POST /requirements`,
  `GET/PUT/DELETE /requirements/{id}`, com filtros `kind` e `status`.
- The system shall suportar critérios de aceite em formato EARS no corpo
  da story (insumo para geração de CTs por IA no M5).
- The system shall parsear e indexar os critérios de aceite EARS da story
  (seção `## Critérios de aceite`, itens `- [EARS-n] ...`) na tabela
  `criteria` com a forma detectada por critério (ubiquitous/event/state/
  unwanted/optional ou nenhuma), expostos por `GET /requirements/{id}/
  criteria`; oferecer no editor templates dos 5 tipos EARS (ID sequencial
  automático) e emitir warnings de lint determinístico no reindex —
  `ears_no_form` (sem verbo modal), `ears_vague` (termo vago configurável em
  `requirements.vague_terms`), `ears_duplicate` — sem NUNCA bloquear o save;
  stories sem a seção ficam fora do lint (opt-in pela presença da seção).
- The system shall expor por story, na matriz de rastreabilidade
  (`GET /metrics/traceability`) e na aba Requisitos, a contagem de critérios
  EARS cobertos (`criteria_covered`/`criteria_total`) — critério coberto =
  com ≥1 CT vinculado via `criteria` — badge exibido só quando a story tem
  critérios.

- The system shall carimbar `created` (data) no frontmatter do requisito na
  criação, indexá-lo e expô-lo na listagem/detalhe.

- The system shall exibir, por story na tela de Requisitos, o estado de
  cobertura (coberta com N CTs vinculados / sem cobertura, badge
  status-dot) e, por epic, o agregado "X/Y cobertas" — mesma fonte da
  matriz de rastreabilidade (`GET /metrics/traceability`), sem cálculo
  paralelo; com o filtro "só sem cobertura".
- The system shall expor `GET /requirements/{id}/chain` devolvendo, para
  uma story, a cadeia completa de rastreabilidade — story → CTs (status de
  documento, último resultado, contagem de evidências, execuções que os
  rodaram) → executions envolvidas → defeitos vinculados — em leitura pura
  sobre as tabelas existentes; a UI oferece a visão "Story 360" navegável a
  partir da aba Requisitos (cada nó abre a tela do item).

### Event-driven

- When uma story referencia um epic inexistente, the system shall
  registrar warning de integridade no reindex (ver `indexing`).
- When um requisito é deletado, the system shall movê-lo para
  `.arbites/trash/`.

### State-driven

- While uma story está `active`, the system shall contabilizá-la no
  denominador da cobertura de requisito (ver `reporting`).

### Unwanted-behavior (must-not)

- The system shall not sincronizar automaticamente com Confluence ou Jira;
  `external_key` e `confluence_url` são referências textuais manuais.

### Optional

- Where `confluence_url` está preenchida, the system may exibir link
  clicável para o detalhe completo da story.

## Acceptance criteria

1. [verified] Criar epic e story pela API gera `.md` válidos em
   `requirements/` com IDs sequenciais — verified by
   `backend/tests/test_requirements.py`.
2. [verified] `GET /requirements?kind=story&status=active` filtra
   corretamente — verified by `backend/tests/test_requirements.py`.
3. [verified] Story com `epic` inexistente aparece em `/warnings` —
   verified by `backend/tests/test_requirements.py`.

4. [verified] Requisito criado recebe `created` e a listagem o expõe —
   verified by `backend/tests/test_requirements.py`.

5. [verified] Story sem CT aparece "sem cobertura" e o filtro isola essas
   stories; story com CT mostra a contagem; epic agrega "X/Y cobertas" —
   dados da matriz, coberta por `backend/tests/test_metrics.py`
   (traceability) + build/revisão visual da tela.

6. [verified] `GET /requirements/{id}/chain` devolve a cadeia completa da
   story (CTs com último resultado + nº de evidências + execuções que os
   rodaram, executions envolvidas, defeitos vinculados) e a soma
   passing/failing/untested; id inexistente → 404 — verified by
   `backend/tests/test_requirements.py`. A visão Story 360 é navegável por
   nó — verified by build + revisão visual (`frontend/src/components/Story360.tsx`).

7. [verified] Critérios EARS são extraídos/indexados com a forma detectada e
   expostos por `GET /requirements/{id}/criteria`; o lint acusa
   `ears_no_form`/`ears_vague`/`ears_duplicate` e uma story legada sem a
   seção não gera nenhum desses warnings; os templates do editor geram IDs
   sequenciais — verified by `backend/tests/test_ears.py` + build + revisão
   visual (`frontend/src/components/Requirements.tsx`).

8. [verified] A matriz e a aba Requisitos expõem por story a contagem de
   critérios EARS cobertos (`criteria_covered`/`criteria_total`, critério com
   ≥1 CT vinculado) — verified by `backend/tests/test_metrics.py`
   (`test_traceability_criteria_coverage`) + build + revisão visual.

## Maturity

**MVP (committed):**

- CRUD de epic/story, vínculo story→epic, tela de lista/editor na UI.
- Story 360 (cadeia completa navegável) e critérios EARS
  (parse/índice/templates/lint) na story.

**Future (aspirational, not committed):**

- Import read-only de cards do Businessmap como requisitos locais (M6).
- Reescrever um critério em EARS pela IA (preview) — o gancho de IA existe;
  fica para uma slice própria.

## Out of scope for this spec

- Matriz de cobertura e métricas (ver `reporting`).
- Test cases (ver `testcases`).
