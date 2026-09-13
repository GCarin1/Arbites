# Delta — testcases (change 0090)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall indexar `needs_rerun` do frontmatter do CT, exibir o
  badge "precisa re-execução" no repositório/board e aceitar o filtro
  correspondente em `GET /testcases`. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Badge e filtro de needs_rerun no repositório — verified
  by `backend/tests/test_testcases.py` + build + revisão visual.
