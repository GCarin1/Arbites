# Change 0197-area-diagnostico-fim-cenario — onde doer

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

*"Quero ter essas informações a partir de filtro: qual cenário falhou mais,
menos, quais os principais erros. Seja criativo — mas isso deve ficar no
final da página."*

Nenhuma dessas perguntas se respondia sem abrir execução por execução. E a
matéria-prima da melhor delas já estava chegando e sendo **jogada fora**: o
relatório Cucumber traz `error_message` no passo que falhou, e a leitura
descartava o campo.

## What

- `ler_cucumber()` passa a guardar a mensagem do passo que falhou — só a
  primeira linha: o resto é pilha de chamada, que agrupa mal e não cabe numa
  tabela. Coluna `error` em `ci_scenarios`.
- `molde_do_erro()`: troca por marcadores o que varia a cada execução
  (números, tempos, endereços, identificadores). Sem isso, "esperado 3,
  recebido 4" e "esperado 7, recebido 9" seriam dois erros diferentes — e
  agrupar pelo texto cru é o mesmo que não agrupar.
- `GET /ci/diagnostic?days=&repo=` e a seção **Onde doer**, no fim da aba:
  cenários que mais falharam (com taxa), erros que mais se repetem (com
  quantos cenários distintos cada um atinge), etapas do pipeline que mais
  quebram, e os que nunca falharam — estes com pelo menos três execuções,
  porque um cenário que rodou uma vez e passou não provou estabilidade
  nenhuma.
- Filtro por repositório: com mais de um repositório de teste, a lista global
  mistura times que não se conhecem, e o plano de correção é de um deles.

## Scope boundaries

Conteúdo de log não é analisado — os `.log` continuam anexos que se abre, não
texto indexado. A mensagem de erro vem do relatório de cenários, que é
estruturado; extrair erro de log livre é outra mudança, com outro risco.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_diagnostico_observabilidade.py`: 12 testes.
- [x] Navegador, com 45 execuções em dois repositórios e erros de verdade:
      20 ocorrências do mesmo timeout em 4 cenários, 16 da mesma asserção.

## Open questions

Nenhuma.
