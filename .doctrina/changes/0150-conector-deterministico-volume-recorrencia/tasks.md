# Tasks — Change 0150-conector-deterministico-volume-recorrencia

- [ ] Definir a operação de lote sobre a porta: conjunto → delta → envio.
- [ ] Preview do delta antes de qualquer escrita no destino.
- [ ] Marcar cada item enviado no momento em que ele vai, para a retomada
      saber onde parou.
- [ ] Tirar do lote o que está em conflito, sem travar o restante.
- [ ] Recuo progressivo em resposta a limite de taxa.
- [ ] Testes: repetir não duplica, retomada não reenvia, conflito sai do
      lote, limite de taxa não perde item.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0150-conector-deterministico-volume-recorrencia/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
