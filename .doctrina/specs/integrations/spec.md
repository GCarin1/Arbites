# Spec — integrations

**Capability:** integrations
**Status:** active
**Implementation:** planned — a identidade externa landa na change 0145; a porta e os adaptadores nas 0148 e 0150
**Realizes:** [SC4] parcialmente (o resgate do Xray foi pontual; aqui o vinculo com o sistema oficial vira permanente) e a decisao de escopo da ADR 0015
**Last updated:** 2026-09-13
**Version:** 0.2.0

## Purpose

O Arbites nao e a ferramenta oficial de gestao de teste da empresa, e nao
tenta ser. Mas e onde o trabalho acontece — o repositorio versionado, o
ciclo, a execucao e a evidencia. Esta capability e a ponte entre os dois
mundos.

Ela guarda TRES coisas e nada mais:

1. **A identidade externa** de cada artefato: o que daqui corresponde a que
   la, em qual sistema, em que revisao, e com que conteudo na ultima
   sincronia. Sem isso nao existe idempotencia — nem a do agente MCP, nem a
   de um conector.
2. **A porta** (`ExternalTracker`) que descreve o que uma ferramenta externa
   consegue representar, com CAPACIDADES declaradas em vez de denominador
   comum (ADR 0015).
3. **A deteccao de conflito**: quando os dois lados mudaram desde a ultima
   sincronia, quem decide e uma pessoa, nunca o sistema.

O que ela NAO faz: transportar. Nos fluxos com humano no meio quem atravessa
as pontas e o agente, via MCP (capability `mcp-server`). O transporte proprio
existe so para volume e recorrencia.

## Requirements (EARS)

### Ubiquitous

- The system shall guardar o vinculo externo de um artefato no frontmatter
  do proprio arquivo — sistema, identificador remoto, revisao remota vista e
  hash do conteudo local na ultima sincronia —, porque o indice e descartavel
  (ADR 0001) e o vinculo nao pode morrer com um reindex.
- The system shall permitir mais de um vinculo por artefato, um por sistema,
  para que a mesma base sirva a uma migracao corporativa sem perder o vinculo
  antigo enquanto o novo nasce.
- The system shall expor a consulta "o que daqui ja esta ligado a que la" e a
  sua inversa "o que ainda nao foi sincronizado com o sistema X", que sao as
  duas perguntas que tornam qualquer escrita idempotente.
- The system shall descrever cada ferramenta externa por um conjunto de
  CAPACIDADES declaradas — se representa caso, execucao, resultado,
  evidencia e pasta, e sob que forma —, em vez de assumir um modelo comum a
  todas.
- The system shall recusar em voz alta, no preview, tudo o que a ferramenta
  de destino nao consegue representar, nomeando o que ficara de fora.
- The system shall oferecer intercambio por arquivo em CSV e Cucumber JSON, nos dois sentidos, como adaptador que implementa a mesma porta dos demais e funciona com qualquer ferramenta que importe planilha, sem credencial e sem chamada de rede.

### Event-driven

- When um artefato local muda depois de sincronizado, the system shall
  passar a considera-lo pendente para aquele sistema, comparando o hash
  atual com o hash da ultima sincronia.
- When o lado remoto mudou de revisao E o lado local mudou de hash desde a
  ultima sincronia, the system shall registrar um CONFLITO em vez de
  escolher um dos lados.

### State-driven

- While existe conflito de sincronia num artefato, the system shall exibi-lo
  na tela Problemas com o diff dos dois lados e tres saidas explicitas —
  manter o local, aceitar o remoto, ou resolver editando —, e nao sincronizar
  aquele artefato ate a escolha.

### Unwanted-behavior (must-not)

- The system shall not resolver conflito automaticamente por regra de
  recencia: ultimo-que-escreve-vence e perda silenciosa de dado, e numa
  ferramenta de rastreabilidade esse e o defeito mais caro que existe.
- The system shall not descartar em silencio um campo que a ferramenta de
  destino nao representa.
- The system shall not replicar workflow, permissao ou hierarquia do sistema
  corporativo: o escopo e artefato de teste e evidencia.
- The system shall not gravar credencial de sistema externo em arquivo do
  workspace; ela vive no keyring do SO (ADR 0008).

## Acceptance criteria

1. [unverified] Um artefato ganha vinculo externo no frontmatter e o vinculo
   sobrevive a um reindex completo — verified by `backend/tests/test_integrations.py`.
2. [unverified] Um artefato pode ter vinculo em dois sistemas ao mesmo tempo,
   e a consulta por sistema devolve so o do sistema pedido — verified by
   `backend/tests/test_integrations.py`.
3. [unverified] Editar um artefato ja sincronizado o faz aparecer na lista de
   pendentes daquele sistema; sincronizar de novo o tira da lista — verified
   by `backend/tests/test_integrations.py`.
4. [unverified] Mudanca dos DOIS lados desde a ultima sincronia produz
   conflito registrado, e nenhum dos lados e sobrescrito — verified by
   `backend/tests/test_integrations.py`.
5. [unverified] O preview de uma ferramenta sem suporte a evidencia nomeia
   explicitamente que a evidencia ficara de fora — verified by
   `backend/tests/test_integrations.py`.
6. [unverified] Exportar e reimportar o mesmo arquivo nao cria duplicata, um CSV com coluna faltando falha nomeando a coluna, e o preview declara que evidencia sai como caminho e nao como anexo — verified by `backend/tests/test_integrations_file.py`.

## Maturity

**MVP (committed):**

- Vinculo externo no frontmatter, multiplos sistemas, consultas de vinculo e
  de pendencia, deteccao de conflito e capacidades declaradas por adaptador.

**Future (aspirational, not committed):**

- Resolucao de conflito campo a campo (hoje e por artefato).
- Mapeamento de campos proposto por IA e aprovado por humano (ADR 0015);
  nasce como configuracao escrita a mao.

## Out of scope for this spec

- O servidor MCP e as suas ferramentas (capability `mcp-server`).
- O transporte em si — adaptador de arquivo (0148) e conector de volume
  (0150) implementam a porta, mas a porta e o vinculo sao daqui.
- A tela de Problemas, que apenas HOSPEDA o conflito (capability
  `workspace-core`).
