# Spec Delta — capability: mcp-server

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/mcp-server/spec.md`

```ops
bump-version minor
append-requirement state: While a configuração do servidor MCP estiver incompleta, the system shall iniciar mesmo assim e responder o motivo por extenso na primeira ferramenta chamada, em vez de encerrar o processo.
append-requirement event: When o diagnóstico do servidor MCP é pedido pela linha de comando, the system shall relatar em texto o endereço configurado, se há credencial e seu comprimento, e o resultado de uma chamada real à instância.
append-requirement unwanted: The system shall not encerrar o processo do servidor MCP por configuração ausente, nem imprimir o valor da credencial em nenhuma saída de diagnóstico.
append-criterion [verified] Sem credencial o servidor sobe e o motivo chega na primeira chamada; recusa por credencial, por módulo desligado e instância inalcançável têm mensagens próprias; e o diagnóstico informa o comprimento da credencial sem nunca imprimi-la — verified by `backend/tests/test_mcp_arranque.py`.
```
