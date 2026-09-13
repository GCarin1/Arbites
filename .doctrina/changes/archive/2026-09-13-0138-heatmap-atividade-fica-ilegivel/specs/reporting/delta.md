# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

```ops
append-requirement ubiquitous: The system shall garantir um tamanho minimo de celula na grade de atividade e rolar a grade horizontalmente dentro do card quando o periodo inteiro nao couber, mantendo a coluna de dias da semana parada e alinhada com as linhas da grade.
append-criterion [unverified] Em 390 px a celula da grade de atividade mede ao menos 10 px de lado, a grade rola dentro do card e a coluna de dias tem a mesma altura da grade; em 1440 px a celula volta a crescer para preencher o card, sem rolagem — verified by `frontend/src/styles.css` + `frontend/src/components/ActivityHeatmap.tsx`.
bump-version minor
```
