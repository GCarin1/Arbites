# Change 0144-estado-vazio-segue-padrao — estado vazio nao segue o padrao das ferramentas de gestao: paragrafo apagado sem titulo nem acao, sem distinguir nunca-teve-nada de filtro-nao-achou, e em cartao de altura fixa que deixa area morta

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** runtime (confident; signals: filtro) — opened anyway (--force)
- **Affects specs:** design-system

## Why

estado vazio nao segue o padrao das ferramentas de gestao: paragrafo apagado sem titulo nem acao, sem distinguir nunca-teve-nada de filtro-nao-achou, e em cartao de altura fixa que deixa area morta

## What

Toda ferramenta de gestão — Jira, Linear, Trello, GitHub — monta o estado
vazio com as mesmas quatro partes, e nenhuma delas é enfeite:

1. **Marca visual** discreta. É o que separa "vazio" de "ainda carregando";
   sem ela, uma lista vazia e uma lista que não chegou são a mesma tela.
2. **Título** dizendo a SITUAÇÃO, não o erro.
3. **Corpo** de uma ou duas linhas: o que mora ali e de onde vem. É o único
   momento em que a pessoa tem tempo de ler o modelo do produto.
4. **Ação** que resolve o vazio. Um vazio sem saída é um beco.

O Arbites tinha só as partes 2 e 3, e em metade das telas nem isso — seis
lugares resolviam com um `<p class="muted">Nenhum X ainda.</p>`. Nenhum
estado vazio oferecia ação.

E faltava a distinção que mais custa caro: **"nunca teve nada" e "o filtro
não achou nada" são vazios diferentes**. Tratados como um só, a pessoa cria
um item que já existe, só porque o recorte o escondia. O primeiro pede criar;
o segundo pede LIMPAR O FILTRO, nunca criar.

- `frontend/src/components/EmptyState.tsx` (novo) — `EmptyState` com as
  quatro partes, e `NoMatches` para o vazio de filtro.
- `frontend/src/styles.css` — `.empty-art`, `.empty-actions`, a variante
  `compact` (sem moldura dupla dentro de card) e o piso de altura da árvore
  que some quando o conteúdo é um estado vazio.
- Aplicado em Test cases, Requisitos, Execuções, Defeitos, Afazeres e nas
  três listas do painel de administração.

**Sobre a área morta:** a altura do estado vazio passa a ser do CONTEÚDO. O
piso de 320 px da árvore existe para ela não pular de altura enquanto
carrega; com um estado vazio dentro, ele virava um quadro alto com um
parágrafo perdido no meio. O branco que sobra ABAIXO do card numa página
curta não é área morta — é uma página curta, e esticar conteúdo para
preencher tela é o defeito oposto.

**Afeta spec:** `design-system` — o estado vazio era citado como componente,
sem dizer do que ele é feito nem que os dois vazios são diferentes.

## Scope boundaries

- Não inventa ação onde não existe próximo passo óbvio: "nenhuma tentativa
  de login recusada" é boa notícia, e um botão ali seria ruído.
- Não mexe nos estados vazios do Dashboard, que são leituras de período e
  não listas de trabalho.
- Não muda nenhuma consulta nem filtro — só o que se vê quando o resultado
  é vazio.

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
- [x] Num workspace novo, as cinco telas de trabalho (test cases,
      requisitos, execuções, defeitos, afazeres) mostram estado vazio com
      marca visual, título, corpo E ao menos uma ação — medido no navegador.
- [x] Com itens no workspace e um filtro que não casa, a tela mostra o vazio
      de FILTRO, cuja ação é limpar o filtro e não criar.
- [x] A árvore com estado vazio dentro tem a altura do conteúdo, sem o piso
      de 320 px.

## Open questions

Nenhuma.
