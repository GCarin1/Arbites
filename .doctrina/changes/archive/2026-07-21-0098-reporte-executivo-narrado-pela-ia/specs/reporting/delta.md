# Delta — reporting (change 0098)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- Where um provider de IA está configurado, the system may gerar um
  resumo executivo narrado (síntese/riscos/recomendação) a partir das
  métricas, defeitos e cobertura do filtro atual — sempre preview editável
  antes de entrar no export PDF/MD; sem provider, o dashboard permanece
  integral. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Resumo gerado com os números reais injetados e incluído
  no export após aceite — verified by
  `backend/tests/test_reporting_summary.py`.
