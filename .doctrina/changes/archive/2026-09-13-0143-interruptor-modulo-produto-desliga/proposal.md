# Change 0143-interruptor-modulo-produto-desliga — interruptor por modulo do produto que desliga a feature de verdade: some do menu, recusa o deep link e bloqueia os caminhos de API do modulo, em vez de apenas exibir um status de desativado

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** admin

## Why

interruptor por modulo do produto que desliga a feature de verdade: some do menu, recusa o deep link e bloqueia os caminhos de API do modulo, em vez de apenas exibir um status de desativado

## What

O painel tinha cinco interruptores, todos de SUPERFÍCIE PERIGOSA — a
capacidade técnica de rodar subprocess, ler o filesystem, abrir o `.env` de
um projeto-alvo, chamar um provider, importar XML. Não havia como desligar
uma FEATURE do produto, e o efeito do que havia parava no meio: desligado, o
interruptor bloqueava a API e escondia o item do menu em três dos cinco
casos, mas NENHUMA rota do cliente era bloqueada. Quem tivesse `#/ia` na mão
abria a tela inteira, com os botões todos lá, e só descobria que a feature
estava desligada quando a primeira chamada voltou 403.

Esta change introduz **módulo** (ADR 0014): uma TELA mais os caminhos de API
que só ela usa. Sete módulos nascem desligáveis — IA, Automação, Migração do
Xray, Decisões, Memória do projeto, Daily e Reuniões. O núcleo não entra:
requisitos, test cases, execuções, dashboard, defeitos, afazeres, auditoria,
problemas, perfil e a própria administração não têm interruptor.

O interruptor vale nas **três camadas**:

1. `backend/arbites/api.py` — as linhas de `_GOVERNED` de cada módulo são
   GERADAS do registro, não escritas à mão: o que a UI esconde e o que o
   servidor recusa saem da mesma lista e não têm como divergir. Esta é a
   única camada que vale como segurança.
2. `frontend/src/App.tsx` — `isReachable` passa a decidir o RENDER, não só o
   menu. Módulo desligado mostra `ModuleOff` e o link não monta a tela.
   `switchesLoaded` evita o pisca-pisca do primeiro render.
3. O menu, como já era.

- `backend/arbites/auth.py` — registro `MODULES` (rótulo, aba, caminhos) e
  `kind`/`tab` na resposta de `list_switches`.
- `frontend/src/switches.ts` (novo) — o canal "releia os interruptores". Sem
  ele o admin desligava e o menu só mudava no recarregamento seguinte, com o
  item ainda clicável nesse meio-tempo. O evento não carrega estado: a
  verdade continua vindo do servidor.
- `frontend/src/components/Admin.tsx` — a tabela de interruptores vira
  **lista de toggles**, separada em "Módulos do produto" e "Superfícies
  perigosas". O botão "Desligar" dizia a AÇÃO; o toggle mostra o ESTADO.
- `backend/tests/test_authorization.py` — módulo desligado recusa todos os
  seus caminhos e não derruba o núcleo; só admin liga e desliga; só admin
  alcança liberar/recusar/desativar/reativar cadastro.

**Afeta spec:** `admin`. **ADR:** 0014.

## Scope boundaries

- O núcleo do produto não ganha interruptor: um que permita se trancar para
  fora do painel é uma armadilha.
- Não muda a semântica dos cinco interruptores de superfície que já existiam.
- Não mexe no estado vazio das demais telas — outra change.
- Não cria papel novo nem muda a tabela de papéis: admin continua sendo
  quem administra.

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
- [x] Módulo desligado responde 403 em TODOS os seus caminhos, leitura e
      escrita, e o núcleo continua respondendo 200 — provado por teste.
- [x] No navegador, desligar o módulo de IA pelo toggle: o item some do
      menu, o link `#/ia` deixa de montar a tela e a chamada
      `/api/v1/ai/providers` responde 403 — os três na mesma volta.
- [x] Religar devolve as três coisas sem recarregar a página nem reiniciar
      o processo.
- [x] `viewer` e `editor` tomam 403 ao tentar ligar/desligar qualquer
      interruptor e em toda rota de gestão de conta — provado por teste.

## Open questions

Nenhuma em aberto, mas uma consequência declarada na ADR 0014 merece ficar
visível: o **Context Pack** mora na tela de IA e não precisa de provider
nenhum, mas vai junto quando o módulo de IA é desligado. É o preço de o
módulo ser a TELA e não o botão. Se isso incomodar na prática, o caminho é
tirar o Context Pack da tela de IA — não afrouxar o interruptor.
