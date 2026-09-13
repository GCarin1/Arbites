# Change 0142-abas-admin-cabem-px — abas do admin nao cabem em 390px e geram rolagem lateral da pagina inteira, e as tabelas densas do admin escondem a coluna de acoes, o que faz as acoes de liberar e desativar cadastro parecerem inexistentes

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** admin

## Why

abas do admin nao cabem em 390px e geram rolagem lateral da pagina inteira, e as tabelas densas do admin escondem a coluna de acoes, o que faz as acoes de liberar e desativar cadastro parecerem inexistentes

## What

Dois defeitos que se somam e deixam o painel inutilizável no celular.

**1. As abas empurram a página.** As quatro abas do admin (Usuários ·
Acessos · Atividade · Sistema) são botões soltos num `.card-head`, não a
faixa de abas do sistema. Em 390 px elas não cabem e, por serem `flex` sem
rolagem, empurram a LARGURA DA PÁGINA: a tela inteira passa a rolar de lado,
o cabeçalho sai do lugar e o card fica cortado. A faixa canônica
(`TabBar`, change 0135) já rola dentro de si; basta usá-la.

**2. A coluna de ações fica fora da tela.** As cinco tabelas do painel são
`table.dense` dentro de `.table-wrap` (`overflow-x: auto`). Em 390 px a
tabela tem ~700 px, a rolagem é do bloco, e a última coluna — a das AÇÕES —
nunca aparece sem rolar. É por isso que "liberar cadastro" e "desativar
conta" parecem não existir no celular: os botões estão lá, à direita do que
se vê. Pior: como `thead` some da vista junto, a coluna visível fica sem
rótulo.

Em tela estreita a tabela densa vira **lista de cartões**: cada linha um
cartão, cada célula com o rótulo da sua coluna ao lado, e as ações no pé do
cartão — o padrão que Jira, GitHub e Linear usam para tabela em celular. É
opt-in por classe (`stack-narrow`) e por `data-label` em cada célula, para
não mexer em tabela que ninguém rotulou ainda.

- `frontend/src/components/Admin.tsx` — faixa de abas pelo `TabBar`; as
  cinco tabelas ganham `stack-narrow` e `data-label` em cada célula.
- `frontend/src/styles.css` — a regra de empilhamento em `max-width: 860px`.

**Afeta spec:** `admin` — o painel não tinha nenhuma regra de tela estreita,
e a alcançabilidade das ações de conta não estava dita em lugar nenhum.

## Scope boundaries

- Não muda nenhuma regra de permissão: quem pode o quê continua decidido na
  tabela `_GOVERNED` do backend.
- Não muda o que as tabelas mostram, só como elas se apresentam quando a
  tela é estreita.
- Não mexe nos interruptores de superfície nem no que eles desligam — outra
  change.

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
- [x] Em 390 px a PÁGINA do admin não rola de lado
      (`documentElement.scrollWidth === innerWidth`) em nenhuma das quatro
      abas — hoje rola.
- [x] Em 390 px todo botão de ação de conta ("Liberar", "Recusar",
      "Desativar", "Reativar", "Encerrar sessões", "Definir senha") está
      dentro da largura da tela sem rolagem lateral nenhuma.
- [x] Em 390 px cada célula mostra o rótulo da sua coluna.
- [x] Em 1440 px as tabelas continuam tabelas, com cabeçalho e colunas.

## Open questions

Nenhuma.
