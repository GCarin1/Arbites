# Tasks — Change 0146-servidor-mcp-local-expondo

- [x] Escrever a spec da capability `mcp-server` (vem no delta ADDED).
- [x] Criar a credencial do agente: modelo, rotas e aceitação no gate como
      alternativa ao cookie, separada da sessão do navegador.
- [x] Subir o servidor MCP local que autentica como sessão do Arbites e
      atravessa o gate existente.
- [x] Expor as seis leituras derivadas, criando como rota normal as que
      ainda não existiam (`/metrics/coverage-gaps`, `/testcases/impact`).
- [x] Separar, no impacto, vínculo por tag de correlação por risco.
- [x] Expor caso de teste como recurso com URI estável.
- [x] Escrever os testes: cobertura, impacto, módulo desligado, log de
      atividade e recusa de contexto sem escopo.
- [x] Conectar de um cliente MCP real e percorrer as ferramentas.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-14-0146-servidor-mcp-local-expondo/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
