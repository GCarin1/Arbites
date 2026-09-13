# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer no assistente de IA uma secao de MCP com o estado do servidor, o bloco de configuracao pronto para colar no cliente com o endereco real da instancia, a credencial do agente com revogacao, a lista do que o agente alcanca separada entre leitura e escrita, e as ultimas chamadas recebidas.
append-requirement ubiquitous: The system shall tratar a permissao do agente como uma unica decisao entre somente-leitura e leitura-e-escrita, com escrita desligada por padrao, em vez de um interruptor por ferramenta.
append-requirement state: While a conta nao e administradora, the system shall exibir o estado e as ferramentas do MCP em modo de leitura, sem permitir mudar o interruptor nem gerar credencial, explicando o motivo.
append-criterion [unverified] O bloco de configuracao traz o endereco real e e copiavel, a credencial aparece uma vez e revoga sem derrubar a sessao do navegador, escrita desligada recusa ferramenta de escrita, e conta nao-admin ve sem poder mudar — verified by `frontend/src/components/AiAssist.tsx` + `backend/tests/test_mcp_server.py`.
bump-version minor
```
