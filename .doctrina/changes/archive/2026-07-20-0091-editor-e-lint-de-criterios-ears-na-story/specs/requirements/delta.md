# Delta — requirements (change 0091)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall parsear e indexar critérios de aceite EARS da story
  (seção `## Critérios de aceite`, itens `- [EARS-n] ...`), oferecer
  templates dos 5 tipos no editor (com ID sequencial automático) e emitir
  warnings de lint determinístico no reindex (frase sem forma EARS, termos
  vagos configuráveis, duplicata) — sem nunca bloquear o save; stories sem
  a seção ficam fora do lint. Where um provider de IA está configurado,
  the system may oferecer "reescrever em EARS" como preview. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Critérios extraídos/indexados, lint acusando problemas
  reais sem falso positivo em story legada, templates gerando IDs —
  verified by `backend/tests/test_ears.py` + build + revisão visual.
