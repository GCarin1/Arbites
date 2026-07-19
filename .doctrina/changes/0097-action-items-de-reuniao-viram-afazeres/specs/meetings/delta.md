# Delta — meetings (change 0097)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall extrair action items de uma reunião (linhas de
  checkbox deterministicamente; IA opcional como preview) e, mediante
  aceite, criar afazeres vinculados à reunião — sem provider, o caminho
  determinístico permanece 100% funcional. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Extração + aceite criam todos vinculados (com e sem
  IA) — verified by `backend/tests/test_meetings.py`.
