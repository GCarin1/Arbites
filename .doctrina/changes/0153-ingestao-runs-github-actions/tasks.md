# Tasks — Change 0153-ingestao-runs-github-actions

- [ ] Guardar marca d'água por repositório/workflow.
- [ ] Listar runs do Actions além dos disparados daqui, filtrando por
      workflow configurado.
- [ ] Ingerir de forma idempotente por `run_id`.
- [ ] Recuperar o intervalo perdido ao voltar, e não só o mais recente.
- [ ] Recuo progressivo em limite de taxa.
- [ ] Testes: cron aparece, repetir não duplica, retomada traz o intervalo.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-09-14-0153-ingestao-runs-github-actions/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
