# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

```ops
bump-version minor
append-requirement state: While a análise de observabilidade não foi disparada, the system shall informar quanto texto ela mandará ao modelo, em caracteres e em estimativa de tokens declarada como aproximada.
append-requirement unwanted: The system shall not deixar o contexto da análise crescer sem teto com a variedade de cenários instáveis e de repositórios; o dossiê é agregado e permanece previsível.
append-criterion [verified] O tamanho é respondido antes da análise; dobrar as execuções não dobra o texto; a lista de instáveis e os recortes de repositório param nos tetos, guardando os novos e os de mais viradas primeiro, e o total real continua declarado — verified by `backend/tests/test_contexto_da_analise.py`.
```
