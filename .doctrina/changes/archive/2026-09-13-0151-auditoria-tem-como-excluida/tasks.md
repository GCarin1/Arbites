# Tasks — Change 0151-auditoria-tem-como-excluida

- [x] Criar `DELETE /audit/{id}` movendo para a lixeira, no mesmo padrão dos
      demais documentos.
- [x] Criar a exclusão em lote por data, que é a resposta ao acúmulo
      automático.
- [x] Pôr as duas na tabela de rotas governadas, restritas a admin.
- [x] Dar a ação de excluir à linha do histórico, com confirmação, e o
      "Limpar rodadas antigas".
- [x] Tratar a exclusão da rodada aberta na tela, voltando para a mais
      recente.
- [x] Empilhar a tabela de histórico em cartão na tela estreita.
- [x] Testes: exclusão vai para a lixeira e restaura, papel não-admin toma
      403, lote por data não leva o que é posterior.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0151-auditoria-tem-como-excluida/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
