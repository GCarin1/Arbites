# Spec Delta — capability: requirements

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/requirements/spec.md`

---

```ops
append-requirement ubiquitous: The system shall exibir a cobertura de cada criterio de aceite individualmente, com os casos que o cobrem e o ultimo resultado deles, porque a contagem por story nao responde se um criterio especifico foi verificado.
append-requirement ubiquitous: The system shall declarar na tela se o requisito foi escrito aqui ou vive num sistema externo, para que a origem seja visivel antes de alguem edita-lo.
append-requirement unwanted: The system shall not aceitar edicao de requisito vinculado a um sistema externo, recusando com o motivo e indicando a remocao do vinculo como saida explicita, porque editar a copia faz os dois lados discordarem sem ninguem ser avisado.
append-requirement ubiquitous: The system shall incluir story sem epic no calculo de cobertura, para que ela nao seja apresentada como descoberta quando esta coberta.
append-criterion [unverified] Criterio sem caso aparece descoberto e criterio com caso falhando nao aparece verificado; requisito vinculado recusa edicao nomeando o sistema; story sem epic coberta nao e dada como descoberta — verified by `backend/tests/test_requisitos_negocio.py`.
bump-version minor
```
