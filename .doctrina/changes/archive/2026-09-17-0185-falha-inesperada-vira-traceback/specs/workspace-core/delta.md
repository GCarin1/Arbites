# Spec Delta — capability: workspace-core

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/workspace-core/spec.md`

---

Quem clicou e caiu num erro não previsto recebia 500 com uma parede de stack
trace: o motivo real ficava enterrado no meio de sessenta linhas de caminho
de biblioteca, e nada dizia o que fazer.

```ops
append-requirement event: When uma exceção não prevista escapa de uma rota, the system shall responder um erro legível com identificador de rastreio e registrar o traceback completo no log sob o mesmo identificador.
append-requirement unwanted: The system shall not repassar na resposta o texto de uma exceção não prevista; ela pode carregar caminho de arquivo, trecho de consulta ou credencial, e essa resposta chega ao navegador.
append-criterion [verified] Uma rota real que levanta exceção responde 500 com código `internal_error` e identificador próprio a cada falha, sem traceback nem o texto da exceção no corpo; o traceback e o texto vão para o log sob o mesmo identificador; e os erros já previstos continuam com a mensagem deles — verified by `backend/tests/test_falha_inesperada.py`.
set-header Last updated: 2026-09-17
bump-version minor
```
