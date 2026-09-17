# ADR 0019 — medida derivada do run é sinal de primeira classe, marcada como derivada

- **Status:** accepted
- **Date:** 2026-09-17
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** `backend/arbites/ci_derivados.py`, `backend/tests/test_sinais_derivados.py`
- **Landed:** 2026-09-17 — `backend/arbites/ci_derivados.py`, `backend/tests/test_sinais_derivados.py`

## Context

A ADR 0016 estabeleceu que **quem produz declara**: o sinal da observabilidade
vem do `arbites.json` que o pipeline publica, e o Arbites nunca inventa a
semântica de um número que encontrou por aí. A regra existe por um motivo
bom e continua valendo: um número solto num arquivo desconhecido não tem nome
nem unidade, e inventar os dois produz um gráfico que parece informação e não
é — o pior desfecho possível numa ferramenta de qualidade.

O efeito prático, porém, foi este: uma instância com **45 execuções
ingeridas, 1367 violações de acessibilidade lidas e 405 cenários extraídos**
mostrava "Sinais no tempo" **vazio**. Toda a matéria-prima estava no disco,
lida e indexada, e o único eixo que faz um dashboard virar observabilidade —
"está piorando?" — não existia. A tela pedia um manifesto que o pipeline
alheio não tem como publicar hoje, e enquanto isso não dizia nada sobre dados
que o Arbites já conhecia com certeza.

Há uma confusão de duas coisas diferentes por trás disso:

1. **Medir o que não se conhece.** Ler `42` de um `metrics.json` qualquer e
   chamar de "latência". Isso é inferir semântica, e continua proibido.
2. **Medir o que já se conhece.** O Arbites sabe quanto durou a execução
   (tem os horários do provedor), quantos cenários falharam (leu o relatório
   Cucumber, cujo formato é documentado) e quantos elementos violam WCAG
   (leu o axe-core, idem). Nomear e datar esses números não é inferência: é
   aritmética sobre fatos que a ferramenta já apurou.

A 0016 não distinguiu as duas, e a proibição da primeira acabou impedindo a
segunda.

## Decision

Existem **duas origens de sinal**, e ambas produzem série:

- **declarado** — do `arbites.json`. Continua sendo a via preferencial e a
  única forma de um pipeline emitir métrica própria (`lcp_ms`, `cobertura`,
  o que for). Semântica de quem produz.
- **derivado** — calculado pelo Arbites a partir do que **ele mesmo** já
  apurou sobre a execução. O conjunto é **fechado e definido no código**, não
  aberto ao conteúdo do artifact: duração, resultado, contagem e taxa de
  cenários, violações de acessibilidade por gravidade, e jobs que falharam.
  Cada um tem nome e unidade fixados pelo Arbites.

Três condições, e as três são parte da decisão:

1. **O nome do declarado vence.** Se o manifesto declara `duracao_s`, o
   derivado de mesmo nome não é emitido. Quem produz sabe mais.
2. **A origem viaja com o sinal** (`source: declarado | derivado`), até a
   tela. Um número derivado apresentado como se o pipeline o tivesse medido
   seria uma mentira de procedência, e procedência é metade do valor de um
   dado de qualidade.
3. **Derivado só existe quando a fonte existe.** Sem relatório Cucumber, não
   há sinal de cenário — zero inventado é pior que ausência, porque zero é um
   ponto no gráfico e ausência não é.

Continua **proibido** derivar sinal de arquivo cuja forma o Arbites não
reconhece. A fronteira é essa: reconhecer um formato documentado é leitura;
adivinhar o significado de um número solto é invenção.

## Consequences

**Ganho.** A série existe desde a primeira ingestão, sem pedir nada ao
pipeline alheio — que é o caso de quem consome repositórios de teste de
terceiros num projeto de micro-frontends. A tela de observabilidade passa a
responder "está piorando?" no dia 1, e não no dia em que alguém conseguir
alterar o workflow de outro time.

**Custo.** O conjunto derivado é código, não configuração: acrescentar uma
medida exige uma mudança no Arbites. Isso é deliberado — um conjunto aberto
voltaria a ser inferência com outro nome.

**Risco aceito.** Duas séries com nomes parecidos (uma declarada, uma
derivada) podem confundir. Mitigado pela regra 1 (o declarado vence o nome) e
pela regra 2 (a origem aparece na tela).

**O que NÃO muda.** Direção e meta continuam sendo configuração de quem
instala (ADR 0016): o Arbites segue sem saber que mais é pior. Um sinal
derivado é um número no tempo, não um julgamento.
