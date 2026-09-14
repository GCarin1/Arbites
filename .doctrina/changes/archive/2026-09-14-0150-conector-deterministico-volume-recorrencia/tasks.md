# Tasks — Change 0150-conector-deterministico-volume-recorrencia

- [x] Definir a operação de lote sobre a porta: conjunto → delta → envio.
- [x] Preview do delta antes de qualquer escrita no destino.
- [x] Marcar cada item enviado no momento em que ele vai, para a retomada
      saber onde parou.
- [x] Tirar do lote o que está em conflito, sem travar o restante.
- [x] Recuo progressivo em resposta a limite de taxa.
- [x] Testes: repetir não duplica, retomada não reenvia, conflito sai do
      lote, limite de taxa não perde item.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0150-conector-deterministico-volume-recorrencia/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
