# Spec Delta — capability: mcp-server

**Operation:** ADDED
**Target spec on apply:** `.doctrina/specs/mcp-server/spec.md`

---

# Spec — mcp-server

**Capability:** mcp-server
**Status:** active
**Implementation:** planned — leituras na change 0146, escritas na 0147, tela na 0149
**Realizes:** a decisao de escopo da ADR 0015 — o agente e a ponte, e o Arbites expoe em vez de transportar
**Last updated:** 2026-09-13
**Version:** 0.1.0

## Purpose

Publicar o workspace para um agente (Cursor, Claude Desktop, qualquer
cliente MCP) que ja alcanca as outras pontas — Businessmap, GitHub — e
consegue costurar as tres numa volta so.

A regra de desenho e uma: **expor o que o agente NAO consegue calcular
sozinho**. Um espelho fino da REST nao agrega — o agente ja sabe chamar
HTTP, e ler o workspace arquivo a arquivo ele tambem sabe. O que ele nao
tem e a resposta DERIVADA: quais criterios EARS estao sem caso, quais casos
um diff afeta, o que ainda nao foi sincronizado com o sistema oficial.

O servidor e um processo local que fala HTTP com a instancia. Ele carrega
uma sessao de verdade e passa pelo MESMO gate de tudo (papel, modulo
desligado, log de atividade — ADR 0014), entao o que o agente faz em nome de
alguem aparece na auditoria como qualquer outra escrita.

## Requirements (EARS)

### Ubiquitous

- The system shall publicar um servidor MCP local que se autentica como uma
  sessao do Arbites e atravessa o mesmo gate de papel, modulo e log de
  atividade das demais chamadas, sem caminho privilegiado proprio.
- The system shall expor como ferramentas de LEITURA as respostas que o
  agente nao consegue derivar do sistema de arquivos: lacunas de cobertura
  por story e por criterio EARS, casos afetados por um conjunto de arquivos
  alterados, casos pendentes de re-execucao, o pacote de contexto de um
  escopo, o relatorio de uma execucao com evidencias, e os vinculos
  externos.
- The system shall expor artefatos estaveis (caso, story, execucao) tambem
  como RECURSOS com URI propria, para que o agente os referencie sem recolar
  o conteudo inteiro na conversa.
- The system shall declarar, em cada ferramenta, se ela le ou escreve, para
  que o cliente possa pedir confirmacao humana so onde ha efeito.
- The system shall exigir escopo (epic, story ou squad) nas ferramentas que
  montam contexto, pela mesma razao que o `context-pack` ja exige: pacote do
  workspace inteiro nao cabe em janela nenhuma e nao ajuda ninguem.

### Event-driven

- When o agente pede o impacto de um conjunto de arquivos alterados, the
  system shall responder os casos ligados por tag de cenario (ADR 0003) e os
  casos correlacionados pelo mapa de risco, distinguindo as duas origens —
  vinculo explicito e correlacao sao confiancas diferentes.

### State-driven

- While o modulo correspondente esta desligado (ADR 0014), the system shall
  recusar as ferramentas MCP daquele modulo com o mesmo erro das rotas HTTP.

### Unwanted-behavior (must-not)

- The system shall not expor uma ferramenta MCP que apenas repita uma rota
  REST sem agregar resposta derivada.
- The system shall not aceitar uma sessao MCP sem identidade: o log de
  atividade precisa dizer em nome de quem o agente agiu.
- The system shall not devolver o workspace inteiro em nenhuma ferramenta de
  contexto.

## Acceptance criteria

1. [unverified] Um cliente MCP lista as ferramentas e obtem lacunas de
   cobertura de uma story real, com os criterios EARS descobertos — verified
   by `backend/tests/test_mcp_server.py`.
2. [unverified] A ferramenta de impacto recebe uma lista de arquivos e
   devolve os casos ligados por tag, separados dos correlacionados por risco
   — verified by `backend/tests/test_mcp_server.py`.
3. [unverified] Com o modulo desligado, a ferramenta MCP correspondente
   recusa com o mesmo codigo de erro da rota HTTP — verified by
   `backend/tests/test_mcp_server.py`.
4. [unverified] Toda chamada MCP aparece no log de atividade com a conta que
   a originou — verified by `backend/tests/test_mcp_server.py`.
5. [unverified] Ferramenta de contexto sem escopo recusa, como o
   `context-pack` ja recusa — verified by `backend/tests/test_mcp_server.py`.

## Maturity

**MVP (committed):**

- Servidor local, leituras derivadas, recursos por URI, gate compartilhado e
  log de atividade.

**Future (aspirational, not committed):**

- Prompts MCP prontos (revisar cobertura, escrever BDD a partir de card).
- Notificacao/subscription para o agente reagir a evento do workspace.

## Out of scope for this spec

- As ferramentas de ESCRITA (change 0147, mesma capability).
- A tela de configuracao do MCP (change 0149, capability `ai-assist`).
- O vinculo externo em si, que e da capability `integrations`.
