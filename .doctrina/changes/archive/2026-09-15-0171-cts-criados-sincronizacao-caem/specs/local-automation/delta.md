# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

Todos os CTs de todos os `.feature` caíam num diretório só. Num repositório
com dezenas de features isso vira uma lista chapada de centenas de arquivos,
sem pista de onde cada caso mora no projeto automatizado.

```ops
append-requirement event: When CTs são criados pela sincronização de `.feature`, the system shall criar uma pasta por arquivo `.feature`, preservando a hierarquia do repositório abaixo da pasta de destino e descartando o prefixo estático do glob.
append-criterion [verified] Dois cenários de `.feature` em níveis diferentes da árvore criam CTs em pastas distintas que espelham o caminho do arquivo, o prefixo estático do glob é descartado, a pasta informada no modal vira a raiz do espelho, e caminho com `..` não escapa da área — verified by `backend/tests/test_pasta_por_feature.py`.
set-header Last updated: 2026-09-15
bump-version patch
```
