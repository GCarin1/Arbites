# Change 0153-ingestao-runs-github-actions — ingestao de runs do github actions que o arbites nao disparou, com recuperacao do que passou enquanto a maquina estava desligada

- **Status:** proposed
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** runtime (confident; signals: github actions) — opened anyway (--force)
- **Affects specs:** local-automation

## Why

ingestao de runs do github actions que o arbites nao disparou, com recuperacao do que passou enquanto a maquina estava desligada

## What

Hoje o Arbites só conhece run que **ele disparou** (`CIManager.dispatch`).
Um cron que nasce no GitHub — que é justamente o que roda toda semana
colhendo telemetria, logs, acessibilidade e prints — é invisível aqui.

Esta change abre o outro sentido: **ingerir run que o Arbites não começou.**

Por *pull*, e não há escolha (ADR 0016): o runner do GitHub não alcança uma
instância local atrás de NAT, então webhook está fora. Polling com a
credencial que já mora no keyring (ADR 0008).

A consequência manda no desenho: **a máquina fica desligada**, e a ingestão
precisa recuperar o que passou. Não é "pega o que houver agora" — é marca
d'água por repositório/workflow, idempotência por `run_id`, e retomada. Ligar
o computador depois de uma semana fora tem que trazer a semana inteira.

Reaproveita o que existe: `list_artifacts`, `download_artifact`, `get_run` e
`get_jobs` do `CIManager` já falam com o Actions.

## Scope boundaries

- Não decide o que fazer com o conteúdo do artifact — isso é a change 0154.
- Não desenha tela nenhuma (change 0155).
- Não muda o disparo por `dispatch`, que continua existindo para quem quer
  rodar a partir do Arbites.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Um run criado por `schedule` no GitHub aparece no Arbites sem
      ninguém ter disparado nada.
- [ ] Ingerir duas vezes o mesmo run não duplica.
- [ ] Com a ingestão parada por 3 runs, religar traz os 3 — não só o último.
- [ ] Resposta de limite de taxa recua e retoma sem perder run.

## Open questions

Nenhuma.
