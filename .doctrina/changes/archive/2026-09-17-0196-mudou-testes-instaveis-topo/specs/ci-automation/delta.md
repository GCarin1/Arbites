# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version patch
append-requirement ubiquitous: The system shall apresentar o estado do período antes das listas de exceção; o que mudou e os cenários instáveis vêm depois dos números que se consulta todo dia.
append-requirement ubiquitous: The system shall declarar, junto da lista de cenários instáveis, o período que a produziu, o critério que define instabilidade e o fato de ser recalculada a cada período.
append-criterion [verified] O painel abre pelos indicadores e traz o que mudou e os instáveis no fim — verified by `frontend/scripts/audita-ordem.mjs`; e a lista de instáveis nomeia o período, o critério e a recalculação, verificado em navegador.
```
