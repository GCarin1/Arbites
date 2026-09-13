# Delta — testcases (change 0089)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall aceitar `quarantine: bool` no frontmatter do CT
  (toggle na UI), indexado, e exibir no detalhe do CT o sinal de flaky
  (alternância de resultado nas últimas execuções, via métrica existente).
  [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Toggle de quarentena persiste no frontmatter e o badge
  flaky aparece para CT alternante — verified by
  `backend/tests/test_testcases.py` + build + revisão visual.
