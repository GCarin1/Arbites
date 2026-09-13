# Change 0151-auditoria-tem-como-excluida — auditoria nao tem como ser excluida: nenhuma rota de delete e o historico cresce sozinho porque abrir a aba dispara rodada nova quando a ultima passou do intervalo

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** audit

## Why

auditoria nao tem como ser excluida: nenhuma rota de delete e o historico cresce sozinho porque abrir a aba dispara rodada nova quando a ultima passou do intervalo

## What

Uma rodada de auditoria é um documento do workspace como qualquer outro —
mora em `audits/AUD-XXXX.md`, é indexada, aparece no histórico. Todo outro
tipo de documento (requisito, caso, execução, defeito, afazer, reunião) tem
rota de exclusão para a lixeira. Auditoria **não tem nenhuma**: só `run`,
`latest`, `history` e `get`. Nem admin consegue apagar.

E tem um agravante que a torna a MAIS necessária das exclusões: **as rodadas
se acumulam sozinhas.** `GET /audit/latest` roda uma rodada nova sempre que a
última passou de `audit.auto_interval_hours` (24h por padrão). Ou seja, basta
alguém abrir a aba a cada dia para a pasta `audits/` crescer para sempre, sem
ninguém pedir. O histórico da tela corta em 200, mas o disco e o índice não
cortam em nada.

Esta change entrega as duas exclusões, no padrão que o resto do produto já
usa (lixeira, nunca apagar direto — `ws.trash`):

- `DELETE /audit/{id}` — uma rodada.
- `DELETE /audit?before=<data>` — todas as rodadas anteriores a uma data, que
  é a resposta prática ao acúmulo automático.

**Só admin.** As duas entram na tabela `_GOVERNED`, como o painel. Uma rodada
de auditoria é um retrato do estado de qualidade num momento — apagar é mais
perto de destruir registro do que de descartar rascunho, e quem faz isso
precisa ser quem administra a instância. Vai para a lixeira, então é
reversível, e a escrita cai no log de atividade como qualquer outra.

Na tela, o histórico ganha a ação de excluir no menu de ações da linha
(padrão da change 0131) com confirmação, e um "Limpar rodadas antigas". A
tabela do histórico também ganha o empilhamento em cartão da change 0142 —
hoje ela é `table.dense` sem `stack-narrow`, então no celular sofre
exatamente o problema que o painel de administração já teve.

**Afeta spec:** `audit`.

## Scope boundaries

- **Não mexe no log de atividade.** Ele é contínuo e imutável de propósito,
  e não tem rota que o edite ou remova — registro que o próprio suspeito
  apaga não prova nada. São duas coisas diferentes com o mesmo nome.
- Não adiciona retenção automática. Apagar sozinho é destrutivo por padrão,
  e quantas rodadas guardar é decisão de produto — fica como pergunta, não
  como default escolhido por mim.
- Não muda como a auditoria é gerada nem o que ela acha.

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
- [x] Excluir uma rodada a tira do histórico e a coloca na lixeira, de onde
      pode ser restaurada.
- [x] `viewer` e `editor` recebem 403 nas duas exclusões.
- [x] Excluir em lote por data remove só o que é anterior, e deixa o resto.
- [x] Excluir a rodada que está aberta na tela não deixa a tela quebrada —
      ela volta para a mais recente.
- [x] Em 390 px a tabela de histórico vira cartão e a ação de excluir fica
      dentro da largura da tela.

## Open questions

**Retenção automática fica em aberto de propósito.** Com a rodada automática
a cada 24h, a exclusão manual resolve hoje mas volta a encher. O caminho
natural seria um `audit.keep_last` no `arbites.yaml`, mas isso é apagar
sozinho — e escolher o número por conta própria seria decidir pelo dono da
instância. Fica registrado para decidir depois de ver o acúmulo real.
