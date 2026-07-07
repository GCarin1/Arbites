# Spec Delta — capability: meetings

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/meetings/spec.md`

---

## Context

M12 entrega a capability: CRUD de reuniões em `meetings/*.md` (tema, data,
corpo), tabela `meetings` no índice, resumo executivo por IA
(`ai.summarize_meeting`, preview), inclusão das reuniões do dia no contexto da
daily (`daily.build_context`/`context_markdown`) e a aba **Reuniões** no
frontend. Isto passa a Implementação de `planned` → `verified` e os três
critérios de `[unverified]` → `[verified]`.

## Header (MODIFIED)

- **Implementation:** verified — M12 (backend/arbites/indexer.py,
  backend/arbites/api.py, backend/arbites/ai.py, backend/arbites/daily.py,
  backend/arbites/workspace.py; frontend Meetings.tsx). ID `MTG-`, arquivos em
  `meetings/`.

## Acceptance criteria (MODIFIED — verificados)

1. [verified] CRUD de reunião (tema/data/corpo) persistido em
   `meetings/*.md` e refletido no índice; listagem filtrável por data —
   verified by `backend/tests/test_meetings.py`.
2. [verified] Resumir uma reunião com um provider (mock) devolve o resumo
   executivo em preview, sem gravar; salvar persiste `summary` — verified by
   `backend/tests/test_meetings.py`.
3. [verified] As reuniões do dia aparecem no contexto da daily daquele dia —
   verified by `backend/tests/test_meetings.py`.
