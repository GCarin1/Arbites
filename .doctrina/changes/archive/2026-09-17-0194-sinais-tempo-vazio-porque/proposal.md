# Change 0194-sinais-tempo-vazio-porque — a série que existia e não aparecia

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

45 execuções ingeridas, 1367 violações de acessibilidade lidas, 405 cenários
extraídos — e **"Sinais no tempo" vazio**. Toda a matéria-prima estava no
disco, lida e indexada, e o único eixo que faz um dashboard virar
observabilidade — *"está piorando?"* — não existia.

A tela pedia um `arbites.json` que o pipeline de outro time não tem como
publicar hoje. Num projeto de micro-frontends, quem consome repositórios de
teste de terceiros ficaria esperando indefinidamente por uma alteração em
workflow alheio.

Eu tinha respondido que isso era por desenho (ADR 0016). Estava meio certo e
meio errado, e a parte errada importa: a 0016 proíbe **inferir semântica** —
ler `42` de um `metrics.json` qualquer e chamar de "latência" —, e isso
continua certo. Mas ela não distinguiu isso de **medir o que já se conhece**.
O Arbites sabe quanto durou a execução (tem os horários do provedor), quantos
cenários falharam (leu o Cucumber, formato documentado) e quantas violações
de WCAG houve (leu o axe-core, idem). Nomear e datar esses números não é
adivinhar — é aritmética sobre fatos já apurados.

## What

- **ADR 0019**: duas origens de sinal, `declarado` e `derivado`, com três
  condições — o nome declarado vence, a origem viaja até a tela, e derivado
  só existe quando a fonte existe.
- `backend/arbites/ci_derivados.py`: o conjunto **fechado** de dez medidas.
- Coluna `source` em `ci_signals`, carregada em toda leitura da série.
- `escrever_run()` emite os derivados; `reprocessar()` os recalcula para o
  que já está no disco, sem rede.
- Tela: nome legível por medida, etiqueta **derivado** com explicação, e a
  mensagem de vazio reescrita — ela dizia "declare o manifesto" quando a
  causa real era não haver execução no período.
- Correção achada por teste: `reprocessar()` abortava quando os anexos não
  estavam no disco, deixando sem série justamente a execução cujos anexos a
  retenção já levou — horário, conclusão e jobs continuam lá.

## Scope boundaries

Direção e meta continuam sendo configuração de quem instala (ADR 0016): um
sinal derivado é um número no tempo, não um julgamento. O conjunto é código,
não configuração — um conjunto aberto voltaria a ser inferência com outro
nome.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_sinais_derivados.py`: 14 testes, incluindo as três
      regras da ADR e o reprocessamento do que já estava ingerido.
- [x] Navegador, com 45 execuções semeadas no formato do relatório: dez
      séries onde antes havia zero, todas marcadas "derivado".
- [x] `audita-estreito.mjs` em 390px: 15 telas, nenhum achado.

## Open questions

Nenhuma.
