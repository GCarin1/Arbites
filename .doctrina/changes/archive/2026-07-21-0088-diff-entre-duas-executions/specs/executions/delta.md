# Delta — executions (change 0088)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall expor `GET /executions/diff?a=&b=` comparando os
  resultados por CT de duas executions (regressed / fixed / added /
  removed / unchanged), e a UI shall oferecer seleção de duas executions
  para visualizar o diff por categoria. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] O diff entre duas executions classifica cada CT na
  categoria correta — verified by `backend/tests/test_executions.py` +
  build + revisão visual.
