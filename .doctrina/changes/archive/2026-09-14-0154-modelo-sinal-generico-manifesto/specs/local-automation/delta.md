# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

```ops
append-requirement ubiquitous: The system shall representar toda medida vinda de uma execucao de CI como sinal generico com nome, valor, unidade e instante, sem conhecer de antemao o tipo da medida, para que o pipeline possa emitir medida nova sem alteracao de codigo.
append-requirement ubiquitous: The system shall aceitar do artifact um manifesto que declara os sinais produzidos e onde estao, e tratar artefato que nao e medida — captura de tela, log, analise em texto — como anexo da execucao e nao como sinal.
append-criterion [unverified] Um sinal nunca visto e ingerido sem mudanca de codigo e fica consultavel por nome e periodo; artifact sem manifesto cai no modo convencao e anuncia que caiu — verified by `backend/tests/test_ci_ingest.py`.
bump-version minor
```
