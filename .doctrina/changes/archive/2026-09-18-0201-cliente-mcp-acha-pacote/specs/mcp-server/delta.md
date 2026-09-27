# Spec Delta — capability: mcp-server

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/mcp-server/spec.md`

```ops
bump-version minor
append-requirement ubiquitous: The system shall ser instalável como pacote, para que o comando do servidor MCP funcione a partir de qualquer diretório — o cliente lança o processo do diretório dele, não do projeto.
append-requirement event: When o diagnóstico da instalação é pedido, the system shall aferir a partir de um diretório diferente do projeto se o módulo do servidor MCP é encontrado, e nomear o conserto quando não for.
append-requirement event: When o diagnóstico do servidor MCP roda sem credencial no ambiente, the system shall avisar que o bloco de ambiente do cliente não vale no terminal e mostrar como passar endereço e credencial na mão.
append-requirement unwanted: The system shall not documentar o servidor MCP sem o diretório de trabalho ou a instalação do pacote; o comando copiado sem eles falha antes de falar protocolo e produz apenas um erro genérico.
append-criterion [verified] O módulo é encontrado a partir de outro diretório quando o diretório de trabalho é declarado ou o pacote instalado; o projeto declara como ser instalado e aceita a versão de Python que roda a suíte; o diagnóstico afere de fora e nomeia o conserto; ele aceita endereço e credencial na mão sem imprimir a credencial; e a documentação traz o diretório de trabalho — verified by `backend/tests/test_mcp_alcancavel.py` e `backend/tests/test_mcp_arranque.py`.
```
