# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

O Kanban resolve os títulos dos casos do ciclo com UMA chamada a
`GET /testcases` e monta o mapa `id → título` na memória. O modo guiado da
change 0113 saiu diferente: ele pede `GET /testcases/{id}` uma vez por caso,
em paralelo.

Num ciclo de vinte casos são vinte requisições onde o Kanban faz uma; numa
regressão de duzentos, duzentas — e o modo guiado existe justamente para a
regressão grande, que é onde a diferença dói. Pior: é uma divergência de
padrão dentro da mesma capability, com duas telas resolvendo o mesmo
problema de dois jeitos.

```ops
bump-version patch
append-requirement ubiquitous: The system shall resolver os títulos dos casos de um ciclo com uma única leitura de `GET /testcases`, tanto no Kanban quanto no modo guiado, em vez de uma requisição por caso.
append-criterion [unverified] Abrir um ciclo resolve os títulos dos seus casos com uma única leitura da lista de casos, e o número de requisições não cresce com o tamanho do ciclo — verified by `frontend/src/components/ExecutionGuided.tsx` + `backend/tests/test_executions_guided.py`.
```
