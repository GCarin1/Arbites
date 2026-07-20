# Delta — requirements (change 0087)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall distinguir na cobertura de uma story o estado
  semântico do último resultado dos CTs vinculados — coberta-e-passando /
  coberta-com-falhas / coberta-nunca-executada / sem cobertura — derivado
  da matriz de rastreabilidade enriquecida com o último resultado por CT
  (fonte única com o dashboard), com filtro por estado. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Os 4 estados de cobertura são derivados corretamente do
  último resultado por CT e exibidos com filtro — verified by
  `backend/tests/test_metrics.py` + build + revisão visual.
