# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall permitir mover uma pasta inteira (drag & drop) para dentro
  de outra pasta sob `testcases/` via `POST /testcases/folders/move`,
  preservando toda a subárvore e reindexando cada `.md` afetado no novo
  caminho (IDs preservados).

### Event-driven

- When o usuário arrasta uma pasta que contém um ou mais casos de teste
  (recursivamente) para dentro de outra pasta, the system shall abrir um
  modal de confirmação informando quantos CTs serão movidos junto, e só
  mover após confirmação explícita.

### Unwanted-behavior (must-not)

- The system shall not aceitar mover uma pasta para dentro dela mesma ou de
  uma pasta descendente (422); nem sobrescrever uma pasta existente com o
  mesmo nome no destino (409).

## Acceptance criteria

8. [verified] Mover uma pasta com CTs para outra pasta preserva os IDs e
   atualiza os caminhos; mover para dentro de si mesma/descendente e para um
   destino já ocupado são rejeitados — verified by
   `backend/tests/test_tc_repository.py`.
