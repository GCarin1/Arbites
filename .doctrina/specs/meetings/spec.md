# Spec — meetings

**Capability:** meetings
**Status:** active
**Implementation:** verified — M12 (backend/arbites/indexer.py, backend/arbites/api.py, backend/arbites/ai.py, backend/arbites/daily.py, backend/arbites/workspace.py; frontend Meetings.tsx). ID `MTG-`, arquivos em `meetings/`
**Realizes:** SC13
**Last updated:** 2026-07-07
**Version:** 0.2.0

## Purpose

Registrar reuniões do QA (tema, data e o que foi falado — descrição breve ou
transcrição) e obter um **resumo executivo** pela IA. Cada reunião é um `.md`
em `meetings/` (fonte de verdade no disco). As reuniões do dia alimentam a
digestão da **daily** (M11) — fechando o loop reunião → daily → afazeres. Sem
provider de IA, a aba é 100% funcional (registro/leitura manual); só o resumo
automático depende da IA (opcional, M5), sempre como preview antes de gravar.

## Requirements (EARS)

### Ubiquitous

- The system shall representar cada reunião como `.md` em `meetings/` com
  frontmatter `id`, `title` (tema), `date`, `summary` (resumo executivo,
  opcional) e corpo com a descrição ou transcrição.
- The system shall expor CRUD `GET /meetings` (filtrável por data),
  `POST /meetings`, `GET /meetings/{id}`, `PUT /meetings/{id}`,
  `DELETE /meetings/{id}`.
- The system shall indexar reuniões (data, tema) para listagem e para o
  contexto da daily.

### Event-driven

- When o usuário solicita resumir uma reunião e há provider de IA
  configurado, the system shall devolver um resumo executivo em preview —
  sem gravar; o usuário aceita salvando em `summary`.

### State-driven

- While há reuniões na data de uma daily, the system shall incluí-las (tema
  + resumo) no contexto daquela daily (M11).

### Unwanted-behavior (must-not)

- The system shall not gravar o resumo da IA sem ação explícita do usuário
  (preview obrigatório).
- The system shall not tornar a aba dependente de IA (registro e leitura
  funcionam sem provider).

### Optional

- Where a transcrição é longa, the system may truncar/resumir apenas o
  necessário para caber no limite do provider (responsabilidade da IA).

## Acceptance criteria

1. [verified] CRUD de reunião (tema/data/corpo) persistido em
   `meetings/*.md` e refletido no índice; listagem filtrável por data —
   verified by `backend/tests/test_meetings.py`.
2. [verified] Resumir uma reunião com um provider (mock) devolve o resumo
   executivo em preview, sem gravar; salvar persiste `summary` — verified by
   `backend/tests/test_meetings.py`.
3. [verified] As reuniões do dia aparecem no contexto da daily daquele dia
   — verified by `backend/tests/test_meetings.py`.

## Maturity

**MVP (committed):**

- CRUD de reuniões, resumo executivo por IA (preview), inclusão no contexto
  da daily.

**Future (aspirational, not committed):**

- Extração de action items da reunião → afazeres; upload/parse de arquivo de
  transcrição; templates de ata.

## Out of scope for this spec

- Gravação/transcrição de áudio (o usuário cola a descrição/transcrição).
- Agendamento/calendário de reuniões futuras.
