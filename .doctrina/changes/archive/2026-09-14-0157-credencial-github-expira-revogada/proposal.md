# Change 0157-credencial-github-expira-revogada — credencial do github que expira ou e revogada vira problema visivel em vez de ingestao que para em silencio

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** runtime (confident; signals: em silencio) — opened anyway (--force)
- **Affects specs:** local-automation

## Why

credencial do github que expira ou e revogada vira problema visivel em vez de ingestao que para em silencio

## What

**O achado da pesquisa sobre o PAT.** Não há data de descontinuação
anunciada para o token classic — a documentação do GitHub apenas *recomenda*
o fine-grained. Mas o risco real para o Arbites não é "o PAT vai acabar", e
sim:

- o fine-grained tem **expiração máxima de 366 dias** (o classic pode não
  expirar), e
- o dono da organização pode **exigir aprovação e revogar** a qualquer
  momento.

Ou seja: a credencial **vai** falhar um dia, por desenho. E hoje o Arbites não
tem história nenhuma para isso — com a ingestão contínua da change 0153, ela
simplesmente pararia **em silêncio**, e alguém descobriria semanas depois ao
notar que a observabilidade congelou.

Esta change transforma isso em problema visível:

- a credencial passa a ter validade conhecida e o Arbites avisa **antes** de
  expirar, não depois;
- `401`/`403` do provedor viram um item na tela **Problemas**, com o motivo,
  e não uma linha de log;
- a ingestão parada por credencial é distinguida de "não há run novo" — são
  estados diferentes e hoje parecem iguais.

Não muda o tipo de token: quem instala escolhe classic ou fine-grained, e o
Arbites lida com os dois. O que muda é ele deixar de confiar que a
credencial é eterna.

## Scope boundaries

- Não migra para GitHub App: é o caminho durável para organização, mas é
  peso grande para uma ferramenta local de uma pessoa. Fica registrado como
  alternativa, não como escopo.
- Não renova credencial sozinho — renovar é ato de quem tem a conta.

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
- [x] Credencial perto de expirar aparece em Problemas antes de expirar.
- [x] `401`/`403` do provedor viram problema com o motivo, e a ingestão
      informa que parou por credencial — não fica igual a "sem run novo".
- [x] Repor a credencial retoma a ingestão do ponto em que parou, sem perder
      o intervalo.

## Open questions

O caminho durável para uma organização é **GitHub App** em vez de PAT:
token de instalação rotaciona sozinho, é aprovado pela organização e tem
escopo mais fino. Não entra aqui porque é peso grande para uma ferramenta
local de uma pessoa — mas se a TI da empresa exigir App, esta é a change que
vira o ponto de entrada.
