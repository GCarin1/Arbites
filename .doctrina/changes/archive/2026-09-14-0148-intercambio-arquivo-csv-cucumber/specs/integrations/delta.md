# Spec Delta — capability: integrations

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/integrations/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer intercambio por arquivo em CSV e Cucumber JSON, nos dois sentidos, como adaptador que implementa a mesma porta dos demais e funciona com qualquer ferramenta que importe planilha, sem credencial e sem chamada de rede.
append-criterion [unverified] Exportar e reimportar o mesmo arquivo nao cria duplicata, um CSV com coluna faltando falha nomeando a coluna, e o preview declara que evidencia sai como caminho e nao como anexo — verified by `backend/tests/test_integrations_file.py`.
bump-version minor
```
