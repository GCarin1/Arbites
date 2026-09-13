# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

O resultado tem `status` e `column`, e a ADR 0005 separou os dois de
propósito: arrastar um caso para "Retest" no quadro muda a coluna sem mentir
sobre o que aconteceu na última execução dele. Todo o resto da interface
conta pela coluna — a barra empilhada, os contadores do Kanban e os
contadores grandes do cabeçalho do ciclo, todos usam `column || status`.

O `progress` que a change 0111 pôs no `GET /executions/{id}` conta por
`status` cru. Reproduzido: um caso que passou e foi arrastado para "Retest"
aparece na coluna Retest do quadro e como **passed** no `progress` da mesma
execution. Dois números para a mesma pergunta, na mesma resposta da API.

Pior: o cabeçalho do ciclo não usa o `progress` que o servidor manda — ele
recalcula por conta própria, pela coluna. O campo existe, o consumidor de
API acredita nele, e a tela mostra outra coisa.

A coluna é a resposta certa, porque é o que o time olha e move. O `progress`
passa a contar por ela, e o cabeçalho passa a exibir o que o servidor
apurou, em vez de manter uma segunda contagem viva no cliente.

```ops
bump-version patch
replace-requirement ubiquitous 17: The system shall apresentar um cabeçalho de progresso do ciclo com a barra empilhada por coluna, um contador grande por coluna, o total de casos e o período com a situação do prazo, exibindo a contagem apurada pelo servidor em vez de recalculá-la no cliente.
append-requirement unwanted: The system shall not apurar o progresso do ciclo por `status` enquanto o quadro conta por coluna; a coluna é o que o time olha e move, e duas contagens da mesma pergunta divergem no primeiro caso arrastado.
append-criterion [unverified] Um caso arrastado para uma coluna diferente do seu status é contado na coluna em que está, e o progresso do ciclo bate com o que o quadro mostra — verified by `backend/tests/test_execution_cycle.py`.
```
