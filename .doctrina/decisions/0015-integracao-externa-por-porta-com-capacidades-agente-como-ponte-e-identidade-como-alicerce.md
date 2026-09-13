# ADR 0015 — Integracao externa por porta com capacidades, agente como ponte e identidade como alicerce

- **Status:** accepted
- **Date:** 2026-09-13
- **Deciders:** Gcarini
- **Supersedes:** 0007 (parcialmente), 0012 (parcialmente)
- **Superseded by:** —
- **Evidence:** n/a — decisao de escopo; landa com as changes 0145-0150
- **Landed:** —

## Context

O Arbites nao pode ser a ferramenta OFICIAL de gestao de teste da empresa —
essa posicao e de um sistema corporativo. Mas ele e onde o trabalho de fato
acontece: o repositorio versionado, o ciclo, a execucao e a evidencia.

Duas decisoes anteriores fecharam esse assunto em direcoes opostas e as duas
envelheceram:

- A **ADR 0007** declarou integracao Jira "fora de escopo permanente" e
  deixou o Businessmap como unica integracao de longo prazo, a especificar.
  O motivo era concreto: a empresa descomissionaria Jira/Xray, e integrar
  com o que vai morrer e esforco perdido.
- A **ADR 0012** congelou a periferia e ABANDONOU o Businessmap, que virou
  non-goal declarado no `product.md`. O motivo tambem era concreto: foi
  especificado e nunca construido, e capability que nao existe nao deve
  ocupar o menu.

O que mudou desde entao: o MCP deixou de ser promessa. Ja existe, em uso na
empresa, servidor MCP do Businessmap com leitura e escrita, assinado pela
pessoa que pediu ao agente e com permissao pedida a cada escrita. O agente
(Cursor) segura varias pontas ao mesmo tempo — Businessmap, GitHub e, se
quisermos, o Arbites.

Isso inverte o problema. A pergunta deixou de ser "quantos conectores o
Arbites precisa escrever" e passou a ser "o que o Arbites precisa EXPOR para
que um agente que ja alcanca as duas pontas consiga sincronizar sem
duplicar".

## Decision

Integracao externa volta ao escopo, com quatro regras.

**1. Porta com CAPACIDADES declaradas, nao denominador comum.**
Nenhuma interface unica serve a todas as ferramentas: o Businessmap e um
quadro Kanban e nao tem caso de teste, execucao nem evidencia como conceito;
o Xray tem os quatro nativos. Cada adaptador declara o que consegue
representar, e o que nao consegue e RECUSADO EM VOZ ALTA no preview — nunca
descartado em silencio.

**2. O agente e a ponte; o Arbites expoe, nao transporta.**
Para os fluxos com humano no meio, quem atravessa as duas pontas e o agente.
O Arbites publica um servidor MCP e nao escreve conector para cada
ferramenta. O MCP expoe o que o agente NAO consegue calcular sozinho
(lacunas de cobertura, impacto de um diff, o que ainda nao foi sincronizado),
e nao um espelho fino da REST — o agente ja sabe chamar HTTP.

**3. Identidade externa e o alicerce, e mora no arquivo.**
Sem saber o que daqui ja esta la, o agente recria o que ja criou — em
conversa nova, sem memoria, isso acontece na primeira semana. O vinculo
(`system`, `id`, `revision`, `synced_hash`) vive no frontmatter (ADR 0001 e
0002), nao so no indice, que e descartavel. `synced_hash` e o que permite
responder "quem mudou desde a ultima sincronia" — sem ele nao existe
deteccao de conflito, so sobrescrita.

**4. Conflito nunca e resolvido sozinho.**
Quando os dois lados mudaram desde a ultima sincronia, o Arbites NAO decide.
O conflito vira um item na tela Problemas, com o diff dos dois lados
(o local vem do git do workspace, ADR 0012/versionamento) e tres saidas
explicitas: fica o meu, fica o deles, edito e resolvo. Ultimo-que-escreve-
vence e perda silenciosa de dado, e numa ferramenta de rastreabilidade isso
e o defeito mais caro que existe.

**Limite de escopo:** o Arbites continua nao sendo a ferramenta oficial e
nao tenta virar uma. Ele nao replica workflow, permissao nem hierarquia do
sistema corporativo — sincroniza artefato de teste e evidencia, e nada mais.

### O que isto supersede

- Da **ADR 0007**, cai "integracao Jira fora de escopo permanente": o
  criterio deixa de ser a ferramenta e passa a ser a porta. Continua valendo
  dela: idempotencia por chave externa, e preview obrigatorio antes de
  escrever.
- Da **ADR 0012**, cai o abandono do Businessmap. Continua valendo dela o
  foco: integracao nao entra no caminho de quem usa o produto para
  repositorio, ciclo e execucao — ela e um modulo desligavel (ADR 0014).

## Alternatives considered

1. **Conector proprio por ferramenta, sem MCP.** Recusado: N conectores e
   como o projeto morre, e a empresa ja tem o MCP do Businessmap em uso. O
   conector deterministico continua fazendo sentido, mas para VOLUME e
   recorrencia — nao como fundacao.
2. **So MCP, sem identidade externa.** Recusado: e o desenho que duplica.
   Sem o vinculo persistido, cada conversa nova recomeca do zero e recria o
   que ja existe.
3. **A IA como motor de sincronia, escrevendo nos dois lados.** Recusado:
   sincronizar e problema deterministico — identidade, idempotencia,
   conflito. LLM e nao-deterministico. A IA entra em tempo de CONFIGURACAO
   (propor o mapeamento de campos de uma ferramenta nova, que e ambiguidade
   real), e o mapa aprovado por um humano vira configuracao aplicada por
   codigo burro.
4. **Denominador comum entre as ferramentas.** Recusado: o denominador comum
   entre um Kanban e um gestor de teste e quase vazio; sobraria titulo e
   descricao, e a evidencia — que e o ponto — ficaria de fora.
5. **Sincronia so por arquivo (CSV/Cucumber), sem API nenhuma.** Recusado
   como UNICA via, mantido como segunda: ela funciona com qualquer
   ferramenta e sem permissao de TI, e por isso e o piso garantido. Mas nao
   da fluxo vivo.

## Consequences

**Positive**

- O que a empresa ve na ferramenta oficial deixa de depender de alguem
  copiar e colar.
- Ferramenta nova passa a custar um MAPA aprovado por humano, nao um
  adaptador escrito a mao.
- O intercambio por arquivo garante que o produto serve mesmo onde a API
  esta trancada.
- O segundo adaptador (arquivo) valida a porta cedo: nao existe abstracao
  antes da segunda implementacao.

**Negative**

- Identidade externa no frontmatter aumenta o ruido do arquivo que a pessoa
  edita no Obsidian.
- Conflito que vai para Problemas e trabalho humano. E o preco de nao perder
  dado, mas e trabalho.
- Manter a porta honesta exige disciplina: a tentacao de "so mais um campo
  so para o Businessmap" e o caminho para a porta virar o formato de UMA
  ferramenta.

**Neutral**

- O servidor MCP e processo local falando HTTP com a instancia, e passa pelo
  mesmo gate de papel, modulo e log de atividade (ADR 0014) — a governanca
  ja existente cobre o agente sem regra nova.
