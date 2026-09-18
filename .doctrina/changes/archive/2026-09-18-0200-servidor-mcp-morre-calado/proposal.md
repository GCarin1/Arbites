# Change 0200-servidor-mcp-morre-calado — "Connection closed" não é um diagnóstico

- **Status:** applied
- **Applied:** 2026-09-18
- **Date:** 2026-09-18
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** mcp-server

## Why

O cliente MCP repetia, a cada tentativa:

```
createClient completed for server: user-arbites, connected=false,
error=MCP error -32000: Connection closed
```

E nada mais. Esse erro é o cliente dizendo **que não sabe**: ele aparece para
qualquer falha no arranque do servidor.

A causa: `client_from_env()` levantava `SystemExit` quando faltava
`ARBITES_TOKEN`. A mensagem saía em **stderr**, que a maioria dos clientes MCP
não exibe, e o processo morria antes de dizer qualquer coisa pelo canal que o
cliente lê. Uma configuração incompleta virava um erro genérico sem pista
nenhuma — reproduzido aqui em um comando.

## What

- **O servidor sobe mesmo sem configuração.** `client_from_env()` nunca
  derruba o processo; devolve um cliente com o impedimento registrado, e o
  motivo chega ao agente escrito por extenso na primeira ferramenta chamada.
  O cliente conecta, e o erro aparece onde a pessoa está olhando.
- **Cada falha ganha a sua mensagem**: credencial recusada (401), módulo
  desligado ou papel insuficiente (403), e instância inalcançável — esta
  última lembrando que, de outra máquina, `127.0.0.1` nunca vai funcionar.
  Antes, um `ConnectError` subia cru e aparecia como traceback de httpx.
- **`python -m arbites.mcp --diagnostico`**: o endereço configurado, se há
  credencial e seu **comprimento** (nunca o valor — este texto existe para ser
  colado num chat), e o resultado de uma chamada real.

## Scope boundaries

Não muda nenhuma ferramenta nem o contrato do protocolo. O servidor continua
sem caminho privilegiado: toda resposta vem de uma rota autenticada (ADR 0015).

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_mcp_arranque.py`: 10 testes.
- [x] Os quatro casos exercitados contra uma instância real: sem token,
      endereço errado, token inválido (401), e o servidor subindo sem morrer
      com stdout limpo — protocolo não pode ser poluído por mensagem.

## Open questions

Nenhuma.
