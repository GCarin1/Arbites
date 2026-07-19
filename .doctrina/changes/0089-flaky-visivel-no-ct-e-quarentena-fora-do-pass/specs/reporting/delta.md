# Delta — reporting (change 0089)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall excluir CTs em quarentena do pass rate e das
  agregações de cobertura semântica, exibindo SEMPRE a contagem "N em
  quarentena" no dashboard com acesso à lista — nunca exclusão silenciosa.
  [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Pass rate ignora quarentenados e o dashboard mostra a
  contagem com drill-down — verified by `backend/tests/test_metrics.py`.
