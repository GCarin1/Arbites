# Design — Change 0002-m1-execucao-manual-executions-kanban-de-resultad

## Approach

O `execution.json` é a fonte de verdade do ciclo (ADR 0001): toda mutação
(status de resultado, step, evidência, defeito vinculado, fechamento)
reescreve o arquivo e reindexa incrementalmente só ele. Um módulo
`executions.py` concentra load/save/mutações e valida as três máquinas de
estado (ADR 0005); a API é uma casca fina. Na criação, os steps do CT são
**snapshotados** de `## Passos` para dentro do resultado — o resultado é
histórico imutável mesmo que o CT mude depois. Evidências vão para
`EXEC-XXXX/evidences/CT-XXXX/` com SHA-256 calculado no upload; o índice
guarda só caminho/hash/mime/timestamp (spec indexing). Kanban no frontend
usa drag nativo HTML5 (sem dependência nova); mover card = POST de status.

## Alternatives considered

- `@dnd-kit/core` para o Kanban — adiado: drag nativo cumpre o requisito
  ("arrastar atualiza o execution.json") sem dependência; dnd-kit entra se
  a UX exigir (touch, reordenação).
- Locks/transações no execution.json — rejeitado na v1: single-user local
  (fora de escopo explícito do intake); último write vence.

## Trade-offs and risks

- Snapshot de steps duplica texto do CT no json — aceito: é o que garante
  histórico fiel (o resultado registra o que foi executado, não o que o CT
  diz hoje).
- Reescrita completa do json a cada mutação — simples e suficiente para
  ~centenas de resultados; se degradar, paginar por resultado é aditivo.

## Decisions to record as ADRs

Nenhuma nova — implementa ADRs 0001, 0005 e 0010 já aceitos.
