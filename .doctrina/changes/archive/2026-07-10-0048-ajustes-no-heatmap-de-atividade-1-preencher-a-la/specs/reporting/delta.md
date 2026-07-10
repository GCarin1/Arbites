# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall aceitar o filtro opcional `year` em `GET /metrics/activity`
  (janela do ano civil, alinhada à segunda-feira), e devolver `years` — os
  anos que têm atividade — para o seletor de ano do heatmap.

### Event-driven

- When o usuário passa o mouse sobre uma célula do heatmap, the system shall
  exibir um tooltip com o número de mudanças (atividade) daquele dia e o
  detalhamento por tipo.

## Acceptance criteria

11. [verified] `GET /metrics/activity?year=` janela o ano civil (alinhado à
    segunda) e a resposta lista os anos com atividade; sem filtro segue os
    últimos ~12 meses — verified by `backend/tests/test_activity_heatmap.py`.
