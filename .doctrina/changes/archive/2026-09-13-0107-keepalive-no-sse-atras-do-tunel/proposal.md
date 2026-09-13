# Change 0107-keepalive-no-sse-atras-do-tunel — Keepalive no SSE atras do tunel

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain; signals: documentar)
- **Affects specs:** local-automation

## Why

Manter o stream de log do run vivo atras do Cloudflare Tunnel: o SSE hoje bloqueia em await sem emitir nada, e um passo silencioso do Behave por mais de cem segundos faz a borda derrubar a conexao ociosa. Emitir comentario de keepalive periodico. Junto disso, corrigir no guia de hospedagem o hostname do dispositivo, que nem sempre e umbrel.local, e documentar a rota por nome de container na rede do app cloudflared, que dispensa publicar a porta no host.

## What

- Delta MODIFIED em `local-automation`: keepalive no stream do run.
- `backend/arbites/api.py`: `SSE_KEEPALIVE_SECONDS` e `asyncio.wait_for` no
  laço do `stream_run`, emitindo comentário SSE no silêncio.
- `backend/tests/test_local_runs.py`: prova do keepalive.
- `docs/self-hosting.md`: o hostname do dispositivo nem sempre é
  `umbrel.local`; nova §2.4 com a rota por nome de container na rede do
  túnel; nota sobre SSE atrás do Cloudflare na seção de operação.
- `docker-compose.yml`: ponteiro para a variante da §2.4.

## Scope boundaries

- Não muda o protocolo do stream nem o cliente: comentário SSE é ignorado
  pelo `EventSource`, então `Automation.tsx` não precisa saber que existe.
- Não torna a variante da §2.4 o padrão do repositório: ela depende de um
  nome de rede interno do Umbrel, que pode mudar entre versões; a porta
  publicada funciona sem saber nada da topologia interna.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `python -m pytest backend/tests -q` passa, incluindo a prova de que
      um run silencioso continua recebendo bytes.
- [x] O novo acceptance criterion de `local-automation` está `[verified]`.
- [x] O `docker-compose.yml` continua YAML válido depois do comentário novo.
- [x] Os blocos de código do guia estão balanceados e os comandos não têm
      escape quebrado.

## Open questions

Nenhuma. O intervalo de 15s foi escolhido com folga larga sobre o limite de
ociosidade do Cloudflare (~100s) e é barato: um comentário por conexão
aberta, só quando não há log para enviar.
