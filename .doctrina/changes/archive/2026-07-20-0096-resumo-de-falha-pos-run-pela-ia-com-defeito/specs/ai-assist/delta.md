# Delta — ai-assist (change 0096)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall expor `POST /ai/analyze-run/{exec_id}` que envia à IA
  o tail do log e os resultados com falha da execution e devolve resumo,
  causa provável e um draft de defeito em preview — o aceite cria o
  defeito vinculado ao CT e à execution; nada é gravado sem aceite.
  [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Análise devolve draft coerente e o aceite grava o
  defeito vinculado — verified by
  `backend/tests/test_ai_analyze_run.py`.
