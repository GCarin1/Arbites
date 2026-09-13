# Change 0139-periodo-ciclo-cabecalho-execucao — periodo do ciclo no cabecalho da execucao e duas caixas de data sem rotulo e de larguras diferentes, precedidas de um traco solto quando sprint e ambiente estao vazios

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

periodo do ciclo no cabecalho da execucao e duas caixas de data sem rotulo e de larguras diferentes, precedidas de um traco solto quando sprint e ambiente estao vazios

## What

O período é o dado mais importante do ciclo depois do nome (ADR 0013: a
execução É o ciclo, e as datas moram nele). No cabeçalho ele aparece como
duas caixas de data **soltas**, sem rótulo visível, medindo 231 px e 195 px —
larguras diferentes para os dois lados do mesmo intervalo. Antes delas vem
`{sprint} · {environment}`, que num ciclo sem esses rótulos renderiza
literalmente `— · —`: dois travessões e um ponto, ocupando espaço para dizer
que não há nada a dizer.

Em 390 px o conjunto quebra em três linhas e fica indistinguível de
"Analisar falha (IA)" e "Fechar execução", que são ações, não campos. Quem
olha não sabe que aquelas duas caixas são início e fim do ciclo — nem que
são um par.

O conserto:

- `frontend/src/components/Executions.tsx`
  - as duas datas passam a ser **um campo só**, rotulado "Período", com as
    pontas ligadas por uma seta: `Período [início] → [fim]`. O par não se
    separa ao quebrar linha, e cada ponta tem o mesmo tamanho.
  - `sprint · environment` só aparece quando há ao menos um dos dois. Sem
    nenhum, não se escreve nada: ausência de rótulo se mostra não mostrando.
- `frontend/src/styles.css` — `.field-group`, o agrupador de rótulo +
  controles que não se separa na quebra de linha, e que serve a qualquer
  cabeçalho com um par de campos.

**Afeta spec:** `executions` — o período já era requisito (ADR 0013);
faltava dizer que ele se apresenta como um campo rotulado, e não como duas
caixas anônimas.

## Scope boundaries

- Não muda o que o período significa, nem a validação de período invertido
  (que continua vindo do servidor em 422).
- Não mexe no cartão de progresso do ciclo logo abaixo, que já mostra o
  prazo por extenso.
- Não mexe nos passos do modal de resultado nem no envio de evidência —
  outra change.

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
- [x] Em 390 px o rótulo "Período" e as duas datas ficam na MESMA linha de
      quebra (o grupo não se parte), e as duas caixas têm a mesma largura.
- [x] Um ciclo sem sprint e sem ambiente não desenha nada no lugar delas —
      nem `—`, nem `·`.
- [x] Em 1440 px o cabeçalho continua numa linha só.

## Open questions

Nenhuma.
