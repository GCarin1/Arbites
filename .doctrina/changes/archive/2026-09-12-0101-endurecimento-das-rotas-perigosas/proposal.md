# Change 0101-endurecimento-das-rotas-perigosas — Endurecimento das rotas perigosas

- **Status:** applied
- **Applied:** 2026-09-12
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** runtime (confident; signals: runner, segredos) — opened anyway (--force)
- **Affects specs:** auth

## Why

Restringir as rotas que executam codigo ou expoem segredos antes de o Arbites ficar acessivel pela internet: runner local (POST /runs/local), navegacao de filesystem (/automation/browse-features), leitura e escrita do .env dos targets, token do GitHub e chaves de IA, e import Xray. Cada uma passa a exigir papel admin e a respeitar um kill switch persistido que o admin liga e desliga, com o estado exposto na API para a UI esconder o que esta desligado.

## What

- Delta MODIFIED em `auth`: alcance de cada papel, superfícies governadas e
  o registro de interruptores.
- `backend/arbites/auth.py`: tabela `switches` no banco durável, registro
  dos interruptores conhecidos e leitura/escrita deles.
- `backend/arbites/api.py`: `require_role` e `require_switch`; recusa
  genérica de escrita para `viewer` no próprio gate de sessão; rotas
  `GET /admin/switches` e `PUT /admin/switches/{name}`.
- `frontend`: o cliente esconde o que o papel não alcança e o que está
  desligado.
- `backend/tests/test_authorization.py`.

## Scope boundaries

- Não valida o conteúdo de um alvo (que `python_path` é aceitável); apenas
  restringe quem pode configurá-lo. Sandbox do subprocess continua fora de
  escopo — a defesa aqui é que só o admin escreve o alvo.
- A tela de administração dos interruptores é do 0102; aqui eles existem na
  API e o frontend apenas respeita o que está desligado.
- Não registra quem executou o quê — isso é o 0103.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `python -m pytest backend/tests -q` passa com o novo
      `backend/tests/test_authorization.py`.
- [x] `npm --prefix frontend run build` passa.
- [x] Os 4 novos acceptance criteria de `auth` estão `[verified]`.
- [x] Uma conta `viewer` não consegue escrever em nenhuma rota, provado por
      varredura das rotas de escrita — não por lista mantida à mão.

## Open questions

Nenhuma. Os interruptores nascem ligados de propósito: desligá-los por
padrão mudaria em silêncio o comportamento da instalação local de hoje. A
recomendação de desligar o que não se usa vai na documentação de exposição
(0105).
