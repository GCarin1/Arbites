# Spec Delta — capability: workspace-core

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/workspace-core/spec.md`

---

```ops
append-requirement ubiquitous: The system shall gerar o arquivo de configuracao inicial comentado e cobrindo todos os blocos que o produto consulta, incluindo os opcionais, porque configuracao que nao aparece no arquivo e configuracao que ninguem descobre.
append-requirement ubiquitous: The system shall declarar no proprio arquivo de configuracao que segredo nao entra nele e onde ele mora, ja que o arquivo fica dentro do workspace versionavel.
append-criterion [unverified] O arquivo gerado traz os onze blocos consultados pelo codigo, nasce comentado, avisa que segredo nao entra nele, carrega como a configuracao padrao e nao sobrescreve um arquivo existente — verified by `backend/tests/test_config_padrao.py`.
bump-version minor
```
