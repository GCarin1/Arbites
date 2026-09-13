# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

```ops
append-requirement ubiquitous: The system shall apresentar o periodo do ciclo como um campo unico rotulado, com inicio e fim ligados e do mesmo tamanho, que nao se separa ao quebrar linha; e omitir sprint e ambiente por inteiro quando nenhum dos dois esta preenchido, em vez de desenhar tracos no lugar deles.
append-criterion [unverified] Em 390 px o rotulo do periodo e as duas datas ficam no mesmo grupo de quebra e as caixas tem a mesma largura; um ciclo sem sprint e sem ambiente nao desenha nada no lugar deles — verified by `frontend/src/components/Executions.tsx` + `frontend/src/styles.css`.
bump-version minor
```
