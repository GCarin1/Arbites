# Spec Delta — capability: mcp-server

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/mcp-server/spec.md`

---

```ops
append-requirement ubiquitous: The system shall expor ferramentas MCP de escrita para caso de teste, resultado de execucao e vinculo externo, cada uma devolvendo um preview do que mudaria antes de aplicar e declarada como escrita para que o cliente peca confirmacao humana.
append-requirement event: When uma escrita MCP alcanca um artefato que ja tem vinculo com o sistema informado, the system shall atualizar o artefato existente em vez de criar outro, para que a mesma chamada repetida nao duplique.
append-requirement unwanted: The system shall not aceitar escrita MCP em artefato com conflito de sincronia aberto, recusando com o motivo em vez de escolher um lado.
append-criterion [unverified] Duas chamadas iguais de criacao com o mesmo vinculo produzem um unico artefato, escrita em artefato em conflito e recusada, e toda escrita aparece no log de atividade com a conta de origem — verified by `backend/tests/test_mcp_server.py`.
bump-version minor
```
