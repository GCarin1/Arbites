# ADR 0013 — Execution e o ciclo datas no proprio ciclo e sprint como rotulo

- **Status:** accepted
- **Date:** 2026-09-13
- **Deciders:** Gcarini
- **Supersedes:** 0010
- **Superseded by:** —
- **Evidence:** —
- **Landed:** 2026-09-13 — `backend/arbites/executions.py`, `backend/arbites/api.py`, `backend/tests/test_execution_cycle.py`

## Context

A ADR 0010 fixou `sprint` e `environment` como texto livre na v1 e previu
que estruturar depois seria aditivo — "as strings existentes viram
referências". O momento chegou: com o time inteiro no mesmo workspace, a
pergunta que a tela precisa responder deixou de ser "qual o nome desta
regressão" e passou a ser "este ciclo está dentro do prazo, quem está
tocando cada caso, quanto falta". Um texto livre não responde nada disso:
não tem começo, não tem fim, e não diz de quem é o caso.

A tentação óbvia é criar a entidade Sprint — cadastro, CRUD, tela, vínculo.
É exatamente a burocracia que a 0010 recusou e que matou o Probatio. A
observação que resolve: a execution **já é** o ciclo. Ela tem dono, tem
conjunto de casos, tem estado, tem fechamento. Faltam a ela as datas.

## Decision

O ciclo é a execution, não uma entidade nova. A execution ganha
`starts_on` e `ends_on` (datas ISO `YYYY-MM-DD`, ambas opcionais, com
`ends_on >= starts_on` quando as duas existem) e cada resultado ganha
`assignee` — o responsável por aquele caso dentro do ciclo, que divide uma
regressão entre duas ou mais pessoas sem duplicar a execution.

`sprint` e `environment` continuam texto livre, agora no papel de **rótulo**
de agrupamento, não de portador de estrutura: as datas moram no ciclo, que
é onde elas têm dono. Nenhum cadastro é criado.

Os três estados do ciclo continuam sendo os que já existem na máquina de
estados da execution — `draft` (planejado), `in_progress` (em andamento) e
`closed` (fechado). O vocabulário do produto passa a ser planejado / em
andamento / fechado; o valor gravado no disco permanece `draft`, porque
renomeá-lo quebraria todo `execution.json` já existente para ganhar
sinônimo. É rótulo de interface, e está registrado aqui para que ninguém
leia a divergência como esquecimento.

## Alternatives considered

1. **Entidade Sprint com cadastro próprio** (datas, CRUD, vínculo da
   execution à sprint) — rejeitada de novo, pelo mesmo motivo da 0010:
   burocracia de telas e vínculos. Além disso duplicaria a data: a sprint
   teria um período e a regressão dentro dela, outro.
2. **Datas em `sprint` como string convencionada** (`"Sprint 42
   (01/09–15/09)"`) — rejeitada: volta a ser texto livre, só que com
   parsing frágil por cima, e nenhum filtro confiável por período.
3. **Renomear `draft` para `planned` no disco** — rejeitada: migração de
   todo `execution.json` existente, e quebra dos critérios já verificados,
   em troca de um sinônimo. O nome de exibição resolve sem tocar no dado.

## Consequences

**Positive**

- O ciclo passa a responder "está no prazo?" e "quem está com este caso?"
  sem nenhuma entidade nova e sem cadastro.
- Estrutura aditiva: `execution.json` sem as chaves novas continua válido e
  é lido como ciclo sem datas e sem responsável.
- O responsável por caso permite dividir uma regressão entre pessoas
  mantendo um único ciclo — e uma única barra de progresso.

**Negative**

- O valor `draft` no disco não é mais o nome que o usuário lê. Fica a
  divergência entre dado e vocabulário, mitigada por este registro.
- Datas por ciclo não dão visão de programa (duas ou mais sprints em sequência);
  quem quiser isso continua agrupando por `sprint` na mão.

**Neutral**

- `sprint` e `environment` seguem texto livre, com os typos que a 0010 já
  aceitou; a diferença é que agora eles não carregam mais estrutura nenhuma.
