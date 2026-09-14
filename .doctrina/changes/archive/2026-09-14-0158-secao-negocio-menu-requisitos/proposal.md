# Change 0158-secao-negocio-menu-requisitos — secao negocio no menu com requisitos, e a tela de requisitos servindo o time de negocio: cobertura por criterio, origem local ou externa visivel, e edicao recusada quando a story vive no sistema oficial

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (confident; signals: criterio)
- **Affects specs:** requirements

## Why

secao negocio no menu com requisitos, e a tela de requisitos servindo o time de negocio: cobertura por criterio, origem local ou externa visivel, e edicao recusada quando a story vive no sistema oficial

## What

Requisito é **insumo do time de negócio** (change 0152): epic e story nascem
com eles, e o que o QA faz é cobri-los. O menu passa a dizer isso com um
cabeçalho próprio — **Negócio** — em vez de deixar Requisitos solto no topo.
Cabeçalho de grupo é o que diz de QUEM é a coisa; um item solto não diz nada.

E a tela passa a servir essa pessoa:

- **Cobertura por CRITÉRIO, não por story.** "Esta story tem 4 CTs" não
  responde a pergunta do negócio, que é *"este critério foi verificado?"* —
  quatro casos podem cobrir o mesmo critério e deixar três descobertos.
  Cada critério mostra o estado (sem caso / nunca executado / com falha /
  verificado), os casos que o cobrem e o último resultado deles.
- **Origem visível.** Escrito aqui × vive no sistema oficial.
- **Edição recusada quando ele vive lá.** Editar a cópia produz divergência
  silenciosa: os dois lados passam a discordar e ninguém é avisado, porque
  nada falha. A recusa ENSINA a saída — remover o vínculo — em vez de só
  barrar, e assim assumir o requisito aqui vira decisão explícita.

## Scope boundaries

- Não muda quem pode criar requisito nem o formato do arquivo.
- Não sincroniza com o sistema externo: só declara a origem e recusa a
  edição. Sincronizar é a porta da ADR 0015.

## Scope boundaries

<!-- Anything adjacent that this change deliberately does NOT touch. -->

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] O menu tem a seção "Negócio" e Requisitos mora nela.
- [x] Critério sem caso aparece descoberto; critério com caso falhando NÃO
      aparece verificado (a média não esconde o defeito).
- [x] Requisito que vive no sistema oficial recusa edição nomeando o sistema,
      e a recusa indica a saída.
- [x] Remover o vínculo devolve a edição.
- [x] Story sem epic coberta não é dada como descoberta.
- [x] Em 390 px a tela não rola de lado.

## Open questions

**Defeito encontrado medindo, e corrigido junto:** a matriz de rastreabilidade
era montada `epic → stories`, então story SEM epic simplesmente não aparecia —
e a tela de requisitos, que a mostra sob "sem epic/", a rotulava "sem
cobertura" mesmo coberta. Cobertura falsa é pior do que cobertura ausente:
alguém age sobre um buraco que não existe. A matriz passou a devolver
`orphan_stories`.

<!-- List unresolved decisions. Empty if none. -->
