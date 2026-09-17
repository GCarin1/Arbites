# Change 0184-saber-qual-codigo-processo — nao da para saber qual codigo o processo esta rodando

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** workspace-core

## Why

nao da para saber qual codigo o processo esta rodando

## What

- `backend/arbites/versao.py` (novo): identidade lida do git — ramo,
  commit curto, data e se há alteração local não commitada. Cacheada, porque
  o processo não troca de código enquanto vive. Sem git (imagem, cópia
  baixada) declara a ausência em vez de inventar.
- `serve` imprime a linha como primeira coisa do terminal.
- `GET /health` devolve os mesmos campos, e continua aberto sem sessão — o
  401 é justamente um dos sintomas que se quer diagnosticar.

## Scope boundaries

- Não substitui `__version__`: ele continua sendo a versão do pacote. O que
  entra ao lado é qual CÓDIGO está rodando, que é outra pergunta.
- Sem escrever arquivo de build no repositório: a fonte é o git, que não
  mente. Um número que alguém precisa lembrar de incrementar fica para trás
  exatamente na hora em que ele importaria.

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

## Open questions

Nenhuma.
