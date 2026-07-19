# Delta — design-system (change 0082)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall usar `SingleRefInput` (busca por id E título) em todo
  campo que referencia uma entidade existente; `<datalist>` fica restrito a
  valores que não são entidades (ex.: squad). [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Campos de referência a entidade usam SingleRefInput em
  todas as telas (sem datalist-por-ID) — verified by build + revisão
  visual + grep.
