# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Context

M9 adiciona um painel de defeitos abertos ao dashboard: contagem por
severidade, por squad e por faixa de aging (0–7 / 8–30 / 30+ dias), mais a
lista dos defeitos abertos. Respeita o filtro de squad já existente
(`GET /metrics/defects?squad=`).

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall expor `GET /metrics/defects` com um resumo dos defeitos
  abertos: contagem total, por severidade, por squad e por faixa de aging
  (dias em aberto), além da lista, filtrável por squad.

## Acceptance criteria (ADDED)

7. [verified] O report de defeitos agrega os defeitos abertos por
   severidade, squad e faixa de aging, e filtra por squad — verified by
   `backend/tests/test_defects.py`.

## Maturity (MODIFIED)

Adicionar ao **MVP (committed)**: painel de defeitos abertos
(aging/severidade/squad). Remover "painel de defeitos" de qualquer menção
como pendência.
