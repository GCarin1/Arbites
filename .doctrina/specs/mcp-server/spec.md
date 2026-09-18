# Spec — mcp-server

**Capability:** mcp-server
**Status:** active
**Implementation:** planned — leituras na change 0146, escritas na 0147, tela na 0149
**Realizes:** a decisao de escopo da ADR 0015 — o agente e a ponte, e o Arbites expoe em vez de transportar
**Last updated:** 2026-09-13
**Version:** 0.4.0

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
- The system shall expor ferramentas MCP de escrita para caso de teste, resultado de execucao e vinculo externo, cada uma devolvendo um preview do que mudaria antes de aplicar e declarada como escrita para que o cliente peca confirmacao humana.
- The system shall ser instalável como pacote, para que o comando do servidor MCP funcione a partir de qualquer diretório — o cliente lança o processo do diretório dele, não do projeto.

### Event-driven

- When o agente pede o impacto de um conjunto de arquivos alterados, the
  system shall responder os casos ligados por tag de cenario (ADR 0003) e os
  casos correlacionados pelo mapa de risco, distinguindo as duas origens —
  vinculo explicito e correlacao sao confiancas diferentes.
- When uma escrita MCP alcanca um artefato que ja tem vinculo com o sistema informado, the system shall atualizar o artefato existente em vez de criar outro, para que a mesma chamada repetida nao duplique.
- When o diagnóstico do servidor MCP é pedido pela linha de comando, the system shall relatar em texto o endereço configurado, se há credencial e seu comprimento, e o resultado de uma chamada real à instância.
- When o diagnóstico da instalação é pedido, the system shall aferir a partir de um diretório diferente do projeto se o módulo do servidor MCP é encontrado, e nomear o conserto quando não for.
- When o diagnóstico do servidor MCP roda sem credencial no ambiente, the system shall avisar que o bloco de ambiente do cliente não vale no terminal e mostrar como passar endereço e credencial na mão.

### State-driven

- While o modulo correspondente esta desligado (ADR 0014), the system shall
  recusar as ferramentas MCP daquele modulo com o mesmo erro das rotas HTTP.
- While a configuração do servidor MCP estiver incompleta, the system shall iniciar mesmo assim e responder o motivo por extenso na primeira ferramenta chamada, em vez de encerrar o processo.

### Unwanted-behavior (must-not)

- The system shall not expor uma ferramenta MCP que apenas repita uma rota
  REST sem agregar resposta derivada.
- The system shall not aceitar uma sessao MCP sem identidade: o log de
  atividade precisa dizer em nome de quem o agente agiu.
- The system shall not devolver o workspace inteiro em nenhuma ferramenta de
  contexto.
- The system shall not aceitar escrita MCP em artefato com conflito de sincronia aberto, recusando com o motivo em vez de escolher um lado.
- The system shall not encerrar o processo do servidor MCP por configuração ausente, nem imprimir o valor da credencial em nenhuma saída de diagnóstico.
- The system shall not documentar o servidor MCP sem o diretório de trabalho ou a instalação do pacote; o comando copiado sem eles falha antes de falar protocolo e produz apenas um erro genérico.

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
6. [unverified] Duas chamadas iguais de criacao com o mesmo vinculo produzem um unico artefato, escrita em artefato em conflito e recusada, e toda escrita aparece no log de atividade com a conta de origem — verified by `backend/tests/test_mcp_server.py`.
7. [verified] Sem credencial o servidor sobe e o motivo chega na primeira chamada; recusa por credencial, por módulo desligado e instância inalcançável têm mensagens próprias; e o diagnóstico informa o comprimento da credencial sem nunca imprimi-la — verified by `backend/tests/test_mcp_arranque.py`.
8. [verified] O módulo é encontrado a partir de outro diretório quando o diretório de trabalho é declarado ou o pacote instalado; o projeto declara como ser instalado e aceita a versão de Python que roda a suíte; o diagnóstico afere de fora e nomeia o conserto; ele aceita endereço e credencial na mão sem imprimir a credencial; e a documentação traz o diretório de trabalho — verified by `backend/tests/test_mcp_alcancavel.py` e `backend/tests/test_mcp_arranque.py`.

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
