# Change 0198-quanto-contexto-vai-ia — quanto isso custa, antes de custar

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ai-assist

## Why

*"Quero saber qual o tamanho do contexto que está sendo passado para a IA; se
for muito será muito chato de API."*

A pergunta é justa e não tinha resposta na tela: quem clicava em **Analisar**
não fazia ideia se aquilo custava um décimo de centavo ou dez.

Medido no caso real (45 execuções, 30 dias): **1.543 caracteres, ≈385 tokens
de entrada** — contra ~128 mil caracteres se fosse o painel cru. O dossiê já
era um recorte agressivo, e a preocupação, embora certa como princípio, não
se materializa hoje.

O que faltava era **dizer isso** e **garantir que continue assim**: o dossiê
não cresce com o número de execuções (é agregado), mas crescia sem limite com
a **variedade** — cenários instáveis e repositórios.

## What

- `tamanho_do_contexto()` e `GET /ci/analysis/size`: caracteres e estimativa
  de tokens, declarada como grosseira.
- A aba Análise mostra isso antes do clique, junto da explicação de por que
  não escala com o número de execuções.
- Tetos: 15 cenários instáveis (os **novos** e os de mais viradas primeiro —
  cortar os 15 primeiros da lista crua entregaria quinze quaisquer), 20
  recortes de repositório, 12 mudanças. O total real continua no dossiê
  (`flaky_total`), para a análise saber que houve corte.

## Scope boundaries

Não muda o que a análise conclui nem o formato do dossiê guardado; só limita
a cauda e informa o tamanho.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_contexto_da_analise.py`: 6 testes, incluindo a
      prova de que 4500 execuções não geram mais texto que 45.

## Open questions

Nenhuma.
