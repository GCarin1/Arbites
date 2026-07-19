# Delta — workspace-core (change 0081)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall expor `GET /trash`, `POST /trash/{name}/restore` e
  `DELETE /trash` (esvaziar), com a moção para a lixeira registrando o
  caminho de origem para restore fiel + reindex do item restaurado.
  [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Item deletado aparece na lixeira, restore o devolve ao
  caminho original (de volta ao índice) e esvaziar limpa — verified by
  `backend/tests/test_trash.py`.
