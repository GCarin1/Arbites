# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

A execution deixa de ser "uma lista de casos com um nome" e passa a ser o
ciclo de teste: tem começo, tem fim e tem gente responsável por cada caso
dentro dela. A ADR 0013 registra por que isso não virou uma entidade Sprint
nova — a execution já era o ciclo, faltavam as datas — e substitui a ADR
0010 nesse ponto: `sprint` e `environment` continuam texto livre, agora no
papel de rótulo de agrupamento, não de portador de estrutura.

O cabeçalho de progresso segue o padrão do Xray: a barra empilhada por
status que já existia passa a vir acompanhada dos contadores grandes por
status, do total de casos e da situação do prazo — o número e a leitura
dele no mesmo lugar.

```ops
bump-version minor
set-header Implementation: verified — M1 + ciclo com datas e responsável por caso (backend/arbites/executions.py, backend/arbites/api.py, frontend/src/components/Executions.tsx)
append-requirement ubiquitous: The system shall guardar no `execution.json` o período do ciclo em `starts_on` e `ends_on` (datas ISO `YYYY-MM-DD`, ambas opcionais), aceitando alteração por `PATCH /executions/{id}`.
append-requirement ubiquitous: The system shall guardar em cada resultado o `assignee` — o responsável por aquele caso dentro do ciclo — e expor `POST /executions/{id}/results/{ct}/assignee` para defini-lo ou limpá-lo.
append-requirement ubiquitous: The system shall exibir o vocabulário do ciclo como planejado (`draft`), em andamento (`in_progress`) e fechado (`closed`), mantendo no disco os valores que a máquina de estados já usa.
append-requirement ubiquitous: The system shall apresentar um cabeçalho de progresso do ciclo com a barra empilhada por status, um contador grande por status, o total de casos e o período com a situação do prazo.
append-requirement event: When `ends_on` é anterior a `starts_on`, the system shall recusar a alteração com 422 em vez de gravar um ciclo que termina antes de começar.
append-requirement event: When o responsável de um caso muda, the system shall registrar evento `{at, who, event: "assignee", testcase_id, to}` no `history[]`, pela mesma razão que status e step já registram.
append-requirement unwanted: The system shall not criar cadastro de sprint, release ou responsável; `sprint` e `environment` seguem texto livre e o `assignee` é o e-mail de uma conta que já existe.
append-criterion [unverified] Uma execution nasce sem período, recebe `starts_on`/`ends_on` por PATCH e sobrevive ao reinício; um período invertido é recusado com 422 — verified by `backend/tests/test_execution_cycle.py`.
append-criterion [unverified] Um caso recebe responsável, o evento entra no `history[]`, o índice enxerga o valor e limpar o responsável volta o caso a sem dono — verified by `backend/tests/test_execution_cycle.py`.
append-criterion [unverified] O cabeçalho do ciclo soma os contadores por status batendo com o total de casos, e um `execution.json` antigo — sem as chaves novas — continua sendo lido como ciclo sem período e sem responsável — verified by `backend/tests/test_execution_cycle.py`.
```
