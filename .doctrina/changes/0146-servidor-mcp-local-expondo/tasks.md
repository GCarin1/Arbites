# Tasks — Change 0146-servidor-mcp-local-expondo

- [ ] Escrever a spec da capability `mcp-server` (vem no delta ADDED).
- [ ] Subir o servidor MCP local que autentica como sessão do Arbites e
      atravessa o gate existente.
- [ ] Expor as seis leituras derivadas, criando como rota normal a que
      ainda não existir na API.
- [ ] Separar, no impacto, vínculo por tag de correlação por risco.
- [ ] Expor caso, story e execução como recursos com URI estável.
- [ ] Escrever os testes: cobertura, impacto, módulo desligado, log de
      atividade e recusa de contexto sem escopo.
- [ ] Conectar de um cliente MCP real e percorrer as seis ferramentas.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0146-servidor-mcp-local-expondo/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
