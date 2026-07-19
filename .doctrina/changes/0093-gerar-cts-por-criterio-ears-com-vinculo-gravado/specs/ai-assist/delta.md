# Delta — ai-assist (change 0093)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- When a story informada tem critérios EARS indexados, the system shall
  oferecer geração de CTs por critério selecionado (prompt focado), e o
  aceite do preview shall gravar `story` + `criteria: [EARS-n]` no CT;
  stories sem critérios mantêm o fluxo de geração da story inteira.
  [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Geração por critério grava o vínculo no aceite; fallback
  para story sem critérios preservado — verified by
  `backend/tests/test_ai_generate.py`.
