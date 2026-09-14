# Tasks — Change 0153-ingestao-runs-github-actions

- [x] Marca d'água por repositório/workflow — DERIVADA do disco (o que já
      tem arquivo em `ci/`), não um contador guardado: contador mente na
      primeira falha no meio e o run perdido some para sempre.
- [x] Listar runs do Actions além dos disparados daqui, filtrando por
      workflow configurado.
- [x] Ingerir de forma idempotente por `run_id`.
- [x] Recuperar o intervalo perdido ao voltar, e não só o mais recente.
- [x] Recuo progressivo em limite de taxa (já no `_request`) e, acima
      dele, parada limpa da ingestão — a retomada não perde run porque a
      marca d'água é o disco.
- [x] Testes: cron aparece, repetir não duplica, retomada traz o intervalo.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-14-0153-ingestao-runs-github-actions/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
