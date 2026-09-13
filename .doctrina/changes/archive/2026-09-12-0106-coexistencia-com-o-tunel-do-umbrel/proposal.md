# Change 0106-coexistencia-com-o-tunel-do-umbrel — Coexistencia com o tunel do Umbrel

- **Status:** applied
- **Applied:** 2026-09-12
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (confident; signals: documentar) — opened as chore
- **Affects specs:** (none — chore)

## Why

Ajustar o empacotamento para reaproveitar o Cloudflare Tunnel que ja roda no UmbrelOS junto do BFFless, em vez de subir um tunel proprio: publicar a porta do Arbites no host, remover o servico cloudflared do compose, e documentar o route especifico ordenado acima do wildcard que o BFFless registra, alem da consequencia de ficar alcancavel pela LAN atras do mesmo login.

## What

- `docker-compose.yml`: publica `8347` no host e deixa de subir um
  `cloudflared` próprio; o bloco do túnel dedicado fica no rodapé como
  alternativa comentada.
- `.env.example`: `TUNNEL_TOKEN` deixa de ser obrigatório.
- `docs/self-hosting.md`: arquitetura de túnel compartilhado, a seção sobre
  o wildcard do BFFless e a ordem dos routes, verificação pela LAN antes de
  mexer na Cloudflare, dois sintomas novos no troubleshooting, e a seção 6
  reescrita (a porta agora é publicada por padrão).

## Scope boundaries

- Não muda código da aplicação: o gate de sessão não sabe por onde a
  requisição entrou, então nada nos changes 0100–0104 depende da topologia.
- Não reabre a decisão da ADR 0011. O que passa a ser compartilhado é o
  **túnel**, que roteia por hostname sem tocar na requisição — não o
  **proxy** do BFFless, que remove headers e tem teto de 60s.
- Não transforma o Arbites num app da loja do UmbrelOS (manifesto, ícone,
  submissão).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `docker-compose.yml` é YAML válido, publica `8347:8347` e não declara
      serviço `cloudflared`.
- [x] O guia não contradiz mais a topologia: nada aponta para um túnel
      próprio como caminho padrão, e a seção 6 descreve a LAN como
      consequência esperada em vez de opção alternativa.
- [x] `doctrina verify` continua verde (o change não toca código).
- [ ] **NÃO VERIFICADO** — a subida real no Umbrel: `docker compose up`, o
      `curl umbrel.local:8347/api/v1/health` e o route ordenado acima do
      wildcard. Não há Docker nem UmbrelOS na máquina onde isto foi escrito;
      são os passos 2.2 e 2.3 do guia, para rodar no servidor.

## Open questions

Nenhuma. O caminho compartilhado foi escolhido pelo usuário sobre o túnel
dedicado: ele já tem o app do Umbrel funcionando, e a exposição na LAN
deixou de ser um problema agora que o gate de sessão vale para qualquer
entrada.
