# Spec Delta — capability: daily

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/daily/spec.md`

---

## Context

M11 entrega a capability: snapshot diário de métricas
(`metrics/AAAA-MM-DD.json`), contexto do dia (todos + atividade + diff +
defeitos) via `backend/arbites/daily.py`, geração por IA (preview,
`ai.generate_daily`), persistência `dailies/AAAA-MM-DD.md`, `GET /dailies`
e a página Daily no frontend (calendário via date picker, gerar/editar/salvar,
action items → todos). Isto passa a Implementação de `planned` → `verified`
e os quatro critérios de `[unverified]` → `[verified]`.

## Header (MODIFIED)

- **Implementation:** verified — M11 (backend/arbites/daily.py,
  backend/arbites/api.py, backend/arbites/ai.py; frontend Daily.tsx).
  IA opcional (reusa provider do M5); snapshots em `metrics/`, dailies em
  `dailies/`.

## Acceptance criteria (MODIFIED — verificados)

1. [verified] Snapshot de métricas é gravado por dia e o contexto expõe o
   diff do dia vs. dia anterior — verified by `backend/tests/test_daily.py`.
2. [verified] O contexto do dia agrega todos (incl. bloqueados), atividade
   (execuções/defeitos do dia) e defeitos abertos — verified by
   `backend/tests/test_daily.py`.
3. [verified] Gerar a daily com um provider (mock) devolve resumo,
   impedimentos, andamento e action items em preview, sem gravar — verified
   by `backend/tests/test_daily.py`.
4. [verified] Salvar a daily persiste `dailies/AAAA-MM-DD.md` e ela aparece
   em `GET /dailies`; aceitar um action item cria um todo — verified by
   `backend/tests/test_daily.py`.
