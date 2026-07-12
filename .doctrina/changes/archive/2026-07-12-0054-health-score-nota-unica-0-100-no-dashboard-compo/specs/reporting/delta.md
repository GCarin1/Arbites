# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /metrics/health` (filtros `sprint`, `days`,
  `squad`) devolvendo uma nota única 0-100 ("Health Score") composta de 4
  componentes com fórmula e peso explícitos cada: cobertura (média de
  cobertura de requisito e de execução), defeitos (100 menos penalidade por
  severidade dos defeitos abertos), automação (pass rate dos runs de
  automação) e dívida de testes (100 menos a média de taxa de bloqueio,
  retrabalho e proporção de CTs flaky).
- The system shall permitir configurar os pesos dos 4 componentes em
  `arbites.yaml` (`health_score.weights`), com default 30/25/25/20
  (cobertura/defeitos/automação/dívida), renormalizado para somar 1.0.

### Unwanted-behavior (must-not)

- The system shall not tratar um componente sem dado disponível como zero;
  ele fica de fora do cálculo (peso dos demais renormalizado), para não
  penalizar — nem inflar — um workspace sem atividade suficiente para
  aquele componente.

## Acceptance criteria

12. [verified] `GET /metrics/health` devolve os 4 componentes com fórmula e
    peso; workspace vazio devolve `score: null`; pesos customizados via
    `arbites.yaml` são respeitados e renormalizados — verified by
    `backend/tests/test_health_score.py`.
