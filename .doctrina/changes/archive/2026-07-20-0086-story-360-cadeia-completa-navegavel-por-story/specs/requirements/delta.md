# Delta — requirements (change 0086)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall expor `GET /requirements/{id}/chain` devolvendo, para
  uma story, a cadeia completa: story → CTs (status de documento, último
  resultado, contagem de evidências) → executions envolvidas → defeitos —
  e a UI shall oferecer uma visão "Story 360" navegável a partir da aba
  Requisitos. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] A cadeia da story (CTs + último resultado + evidências +
  executions + defeitos) é devolvida pelo endpoint e renderizada navegável
  no painel 360 — verified by `backend/tests/test_requirements.py` + build
  + revisão visual.
