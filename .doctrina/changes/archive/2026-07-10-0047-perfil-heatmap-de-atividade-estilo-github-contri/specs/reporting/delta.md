# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /metrics/activity` que agrega a atividade de QA
  por dia nos últimos ~12 meses (janela alinhada à segunda-feira, para a grade
  Seg→Dom × semanas), somando por dia: casos executados (transições de
  resultado), bugs abertos, CTs e requisitos criados e runs de automação;
  devolvendo apenas os dias com atividade (o cliente preenche os zeros) mais os
  totais do período.

## Acceptance criteria

10. [verified] `GET /metrics/activity` agrega os sinais datados por dia
    (casos executados/bugs/CTs/requisitos/runs), com a janela começando numa
    segunda-feira e cobrindo ~53 semanas, e devolve os totais — verified by
    `backend/tests/test_activity_heatmap.py`.
