# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version patch
append-requirement event: When um artifact chega sem manifesto, the system shall reconhecer o relatório Cucumber pela forma do conteúdo — uma lista de features com `elements` —, e não pelo nome do arquivo.
append-requirement event: When o operador pede o reprocessamento, the system shall reler os anexos já gravados no disco e refazer apenas o que é derivado deles, sem nenhuma chamada externa.
append-requirement unwanted: The system shall not classificar um anexo por um nome que o conteúdo desmente; um `result.json` que não é uma lista de features não é um relatório Cucumber, e chamá-lo assim troca um silêncio por uma mentira.
append-requirement unwanted: The system shall not sobrescrever no reprocessamento o que veio do provedor — conclusão, commit, horários —, porque esses campos não estão nos anexos e regravá-los só pode perder informação.
append-criterion [verified] O relatório Cucumber é reconhecido com qualquer nome de arquivo, JSON que não tem a forma não vira cenário, arquivo grande demais não é desserializado, o manifesto declarado continua vencendo a forma, e o reprocessamento do disco recupera o cenário perdido sem tocar nos campos do provedor e sem mudar nada na segunda passada — verified by `backend/tests/test_cenarios_por_forma.py`.
```
