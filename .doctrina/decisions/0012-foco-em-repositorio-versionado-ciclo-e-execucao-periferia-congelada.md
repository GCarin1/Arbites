# ADR 0012 — Foco em repositorio versionado ciclo e execucao periferia congelada

- **Status:** accepted
- **Date:** 2026-09-13
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de escopo; a implementação é a marcação das specs e o reagrupamento da navegação
- **Landed:** —

## Context

O Arbites cresceu em 26 capabilities e 18 abas de navegação. Nada disso foi
construído por acidente — cada peça resolveu um problema real do QA que a
usa. Mas o conjunto deixou de descrever um produto e passou a descrever uma
coleção: `api.py` chegou a 3.916 linhas concentrando tudo, e as três maiores
telas do frontend somam 4.073 linhas, sendo que a maior delas (automação)
não pertence ao que o autor descreve quando explica o que o Arbites é.

Ao ser perguntado diretamente, o autor definiu o produto como **repositório
de casos de teste e execução, com ciclo, versionamento e IA como ajuda**.
Confrontada com as 26 capabilities, essa definição cobre menos da metade
delas.

O antecessor deste projeto (Probatio) falhou por escopo aberto e simultâneo
demais — a lição está registrada no `product.md`. O risco aqui não é
repetir aquele erro pela porta da frente (o Arbites entregou em milestones),
e sim pela dos fundos: manter dezoito frentes vivas ao mesmo tempo, cada uma
exigindo atenção, até que nenhuma fique boa.

Uma observação sobre o custo do que já existe: nada disso é desperdício. As
capabilities fora de foco funcionam, têm testes e são usadas. O problema não
é a existência delas; é a atenção que elas disputam.

## Decision

O escopo ativo do Arbites passa a ser:

**Núcleo** — `testcases`, `executions`, `requirements`, `defects`,
`ai-assist`, `reporting`.

**Infraestrutura** — `workspace-core`, `indexing`, `auth`, `admin`, `audit`,
`design-system`, `home`, `profile`, `segmentation`.

**Congelado** — `meetings`, `daily`, `decisions`, `project-memory`,
`risk-map`, `xray-migration`, `local-automation`, `ci-automation`.

**Enterrado** — `businessmap`, que nunca saiu de `planned`.

**Mantido por decisão explícita** — `todos`.

"Congelado" tem um significado preciso, e é ele que faz esta decisão ser
barata: a spec recebe `Status: deprecated`, o código **permanece**, as rotas
**continuam respondendo**, os testes **continuam rodando no gate**, e o dado
de quem já usou **não é tocado**. O que muda é que essas capabilities saem
da navegação principal (vão para um agrupamento "Mais") e deixam de receber
investimento: nenhuma feature nova, só correção se algo quebrar.

Descongelar é uma decisão de uma linha — outro ADR que supersede este.

## Alternatives considered

1. **Remover código, specs e rotas das capabilities fora de foco** —
   rejeitado. Semanas de trabalho para produzir uma perda: quem já registrou
   reuniões, dailies e decisões perderia o histórico, e o `product.md`
   promete que tudo que existe na interface existe no disco. Apagar features
   que funcionam para "focar" é confundir foco com destruição.
2. **Não fazer nada e só priorizar mentalmente** — rejeitado. Foi o que
   vinha acontecendo, e o resultado são 18 abas competindo. Sem uma marcação
   explícita, a próxima sessão (humana ou de agente) lê 26 specs `active`
   como 26 frentes vivas.
3. **Esconder da navegação sem marcar as specs** — rejeitado pela metade:
   esconder é necessário mas não suficiente. Uma spec `active` que ninguém
   pretende evoluir é uma mentira documentada, e o `doctrina validate` a
   trata como compromisso vivo.
4. **Congelar também `todos`** — rejeitado por decisão explícita do autor,
   que a considera útil no dia a dia. Fica no escopo ativo apesar de não
   pertencer ao núcleo declarado.

## Consequences

**Positive**

- A navegação passa a refletir o produto: o núcleo em primeiro plano, o
  resto acessível mas fora do caminho.
- Quem chega ao repositório — pessoa ou agente — lê nas specs o que está
  vivo, em vez de deduzir.
- O investimento concentra no que o autor identificou como a tese:
  repositório versionado, ciclo, execução.

**Negative**

- Oito capabilities passam a envelhecer. Dependências desatualizam, e um dia
  alguma vai quebrar sem que ninguém esteja olhando.
- SC5 e SC6 (automação local e GitHub Actions) continuam sendo critérios de
  sucesso entregues, mas de uma área congelada — o `product.md` precisa
  dizer isso, senão vira roadmap fantasma.
- O keepalive do SSE (change 0107), escrito dois dias antes desta decisão,
  serve a uma capability que congela. Não foi desperdício — achou um bug
  real —, mas ilustra o custo de decidir foco tarde.

**Neutral**

- O código congelado continua no gate: 393 testes seguem rodando, inclusive
  os das áreas congeladas. Isso é de propósito — congelado não é abandonado.
- A `xray-migration` provavelmente já cumpriu seu papel (era uma janela de
  tempo antes do descomissionamento); congelá-la só formaliza o que os
  fatos já decidiram.
