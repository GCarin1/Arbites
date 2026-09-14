# ADR 0016 — Observabilidade e sinal no tempo com descida ate o artefato, ingerido por pull

- **Status:** accepted
- **Date:** 2026-09-14
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisao de escopo; landa com as changes 0153-0157
- **Landed:** —

## Context

O Dashboard responde "como esta agora": tendencia, mapa de risco, matriz de
rastreabilidade, defeitos abertos. E um RETRATO, e o publico dele e quem
pergunta o estado — em geral um gestor.

O que falta e outra coisa. Existe um pipeline no GitHub Actions que roda por
cron e produz, a cada volta, muito mais do que resultado de teste: telemetria,
logs, acessibilidade, prints, e uma analise de IA em Markdown. Hoje nada
disso chega ao Arbites, por duas razoes distintas:

1. O Arbites so conhece run que ELE disparou (`CIManager.dispatch`). Um cron
   que nasce no GitHub e invisivel aqui.
2. Mesmo que chegasse, a ADR 0006 fixou a coleta em UM formato — Cucumber
   JSON. Telemetria e acessibilidade nao cabem nele.

E o Dashboard nao e o lugar: ele responde outra pergunta, para outro publico.

## Decision

**Observabilidade e sinal no tempo com descida ate o artefato.** Tres regras.

**1. Sinal generico, nao um schema por tipo.**
Todo numero que o pipeline produz vira `(run, kind, name, value, unit, at)`.
Acessibilidade e `kind=a11y, name=violations.critical`; telemetria e
`kind=telemetry, name=lcp_ms, unit=ms`. O Arbites NAO conhece "acessibilidade"
nem "lighthouse" — se conhecesse, cada sinal novo viraria codigo novo, e o
pipeline deixaria de poder evoluir sozinho. Artefato que nao e numero (print,
log, o .md da analise) e ANEXO da run, nao sinal: ele se le, nao se plota.

**2. Quem produz DECLARA, por manifesto.**
O artifact carrega um manifesto dizendo quais sinais tem e onde. Nao por
convencao de nome de arquivo: convencao acopla os dois lados e quebra em
silencio quando alguem renomeia. E o mesmo principio da porta com
capacidades da ADR 0015 — quem produz declara o que produziu.

**3. Ingestao por PULL, e nao ha escolha.**
O runner do GitHub nao alcanca uma instancia local atras de NAT, entao
webhook esta fora. O Arbites faz polling com a credencial que ja mora no
keyring (ADR 0008). A consequencia manda no desenho: a maquina fica
desligada, e a ingestao PRECISA recuperar o que passou — idempotente por
`run_id` e retomavel por marca d'agua, nunca "pega o que houver agora".

**Observabilidade e uma TELA PROPRIA, e o Dashboard continua existindo.**
Publicos diferentes: o Dashboard e o retrato para quem pergunta; a
observabilidade e a tela que o QA abre todo dia para ver O QUE MUDOU. Fundir
as duas produziria uma que nao serve bem a ninguem.

**Toda visao responde uma pergunta acionavel.** Observabilidade sem pergunta
e mural de graficos. Bloco que nao responde "o que quebrou desde ontem",
"que teste virou instavel", "a acessibilidade regrediu" nao entra.

### Relacao com a ADR 0006

A 0006 continua valendo no que decidiu: coleta por ARTIFACT (e nao por log ao
vivo), pela restricao real da API — log de job so existe depois que o job
termina. O que esta ADR acrescenta e que o artifact deixa de ter UM formato
fixo (Cucumber JSON) e passa a ser descrito por manifesto. O Cucumber JSON
vira um sinal entre outros, com o mesmo parser de hoje.

## Alternatives considered

1. **Expandir o Dashboard em vez de criar tela.** Recusado: sao perguntas e
   publicos diferentes. Um retrato com eixo temporal enfiado dentro vira
   ruim nas duas coisas.
2. **Um schema por tipo de sinal (tabela de acessibilidade, tabela de
   telemetria).** Recusado: cada sinal novo viraria migracao e codigo. O
   pipeline tem que poder emitir uma metrica nova sem esperar release do
   Arbites.
3. **Webhook do Actions chamando o Arbites.** Recusado: instancia local atras
   de NAT nao e alcancavel pelo runner. Fica registrado como caminho natural
   se um dia houver instancia publica.
4. **Convencao de nome de arquivo em vez de manifesto.** Recusado como
   desenho principal: acopla os dois lados e quebra calado. Aceito como
   FALLBACK quando o workflow nao pode ser alterado — mas anunciado como
   fallback, nao como contrato.
5. **Guardar tudo para sempre.** Recusado: um cron diario com prints enche
   disco, e "decidir depois" e como se descobre o problema tarde. A retencao
   entra no mesmo escopo (change 0156), nao como promessa futura.

## Consequences

**Positive**

- O pipeline pode emitir sinal novo sem release do Arbites.
- O que o cron ja produz e jogado fora hoje passa a ter historia.
- Uma regressao de acessibilidade ou de tempo deixa de depender de alguem
  abrir o artifact do Actions e comparar na mao.

**Negative**

- Sinal generico nao sabe a semantica: o Arbites nao tem como dizer que
  `lcp_ms` maior e pior sem alguem declarar a direcao. Isso e configuracao,
  e configuracao e trabalho de quem instala.
- Pull significa atraso e teto de taxa, e significa que a maquina desligada
  atrasa a ingestao — nao perde, mas atrasa.
- Guardar print e log tem custo de disco que cresce todo dia.

**Neutral**

- A credencial do GitHub passa a ser caminho critico continuo, e nao so no
  momento de disparar um run: expiracao e revogacao viram problema visivel
  (change 0157).
