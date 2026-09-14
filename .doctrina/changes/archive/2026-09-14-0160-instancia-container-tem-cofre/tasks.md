# Tasks — Change 0160-instancia-container-tem-cofre

- [x] Ler a credencial deixa de explodir onde não há cofre: ausência é
      resposta ("não há credencial"), não acidente.
- [x] Guardar recusa com 409 explicando a saída, em vez de 500.
- [x] Variável de ambiente como origem da credencial (ADR 0017), com
      precedência sobre o cofre.
- [x] A falta de cofre vira problema na tela, com o remédio.
- [x] `docker-compose.yml` e README documentam a variável.
- [x] Ícone da aba Observabilidade, que faltava desde a change 0155 — e o
      fallback de ícone ausente deixa de ser um vazio invisível.
- [x] Testes: a regressão exata (/warnings 200), recusa ao gravar, token pelo
      ambiente, valor nunca volta, nada toca o disco do workspace.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-14-0160-instancia-container-tem-cofre/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
