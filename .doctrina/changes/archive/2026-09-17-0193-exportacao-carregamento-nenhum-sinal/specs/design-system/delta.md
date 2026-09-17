# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

```ops
bump-version minor
append-requirement event: When uma exportação é pedida, the system shall mostrar progresso enquanto o arquivo é gerado e transferido, desabilitando os disparadores até terminar, e entregar o arquivo com o nome que o servidor sugeriu.
append-requirement state: While uma tela ainda não tem dado para mostrar, the system shall exibir o esqueleto do conteúdo que virá, em vez de uma frase solta.
append-requirement unwanted: The system shall not exibir porcentagem de progresso quando o tamanho da resposta é desconhecido; uma barra que promete um número inexistente é pior que uma que só diz que está indo.
append-criterion [verified] A exportação devolve tamanho e nome de arquivo em todos os formatos, inclusive num período sem dado — verified by `backend/tests/test_export_progresso.py`; e a barra em largura de telefone não estoura nem sobrepõe texto — verified by `frontend/scripts/audita-estreito.mjs`.
```
