# Change 0108-caminho-sem-dominio-no-guia — Caminho sem dominio no guia

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain; signals: documentar) — opened as chore
- **Affects specs:** (none — chore)

## Why

Documentar a exposicao sem dominio: rota privada do tunel mais cliente WARP, com o passo de split tunnels que costuma passar despercebido, e o registro de que o quick tunnel do trycloudflare nao serve para esta aplicacao porque nao suporta SSE e o log ao vivo da automacao depende disso.

## What

- `docs/self-hosting.md` §2.5: rota privada do túnel + WARP, para expor sem
  domínio nenhum. Inclui o passo de Split Tunnels (o WARP exclui faixas
  privadas por padrão, então ignora justamente o IP que se quer alcançar) e
  as duas consequências: cliente obrigatório em cada dispositivo, e sem TLS
  no trecho final.
- Aviso na §2.3 de que ela exige domínio, com ponteiro para a §2.5.
- Aviso na §2.4 de que ela **não** combina com rota privada — sem porta
  publicada não há IP:porta para o WARP alcançar.
- Registro de que o quick tunnel (`trycloudflare.com`) não serve para esta
  aplicação: a documentação da Cloudflare lista "no Server-Sent Events
  support", e o log ao vivo da automação é SSE.
- Renumeração: o túnel dedicado passa de §2.5 para §2.6.

## Scope boundaries

- Não muda código nem compose: a rota privada alcança a porta que o compose
  já publica no host.
- Não cobre a configuração do Zero Trust além do necessário para o acesso
  (device enrollment e split tunnels); políticas de Access ficam de fora.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Blocos de código do guia balanceados e referências cruzadas entre
      §2.3, §2.4, §2.5 e §2.6 coerentes após a renumeração.
- [x] `doctrina verify` continua verde (o change não toca código).
- [ ] **NÃO VERIFICADO** — o caminho em si (rota privada, enrollment, split
      tunnels, WARP). Depende da conta Cloudflare e do Umbrel do usuário;
      são os passos da §2.5.

## Open questions

Nenhuma. O quick tunnel foi descartado por um fato da documentação da
Cloudflare, não por preferência: sem SSE, o log ao vivo do runner não
funciona.
