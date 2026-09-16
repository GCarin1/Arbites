# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

A evidência só existia dentro da descida: para ver o print da falha era
preciso já saber em qual execução ela aconteceu — o que inverte a ordem
natural, porque muitas vezes é o print que diz onde olhar.

```ops
append-requirement ubiquitous: The system shall responder os anexos de todas as execuções do período como uma superfície própria, filtrável por tipo e por repositório de origem, e restringível às execuções que falharam.
append-requirement ubiquitous: The system shall entregar em cada evidência o contexto da execução que a produziu — identificador, resultado, repositório de teste, repositório de origem e data — porque um anexo sem execução não é evidência de nada.
append-requirement unwanted: The system shall not cortar a lista de evidências em silêncio nem deixar o limite pedido virar varredura da base; a lista anuncia quando foi truncada e o limite tem teto próprio.
append-criterion [verified] Cada evidência traz o contexto da execução; o recorte por falha e os filtros de tipo e origem funcionam; a ordem é da mais recente para a mais antiga; o resumo por tipo não encolhe com os filtros; o truncamento é anunciado e o limite tem teto; e o caminho do anexo não escapa de `ci/` — verified by `backend/tests/test_evidencias_periodo.py`.
set-header Last updated: 2026-09-16
bump-version minor
```
