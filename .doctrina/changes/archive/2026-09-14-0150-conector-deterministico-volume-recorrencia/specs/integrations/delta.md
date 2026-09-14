# Spec Delta — capability: integrations

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/integrations/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer envio em lote de um ciclo inteiro para o sistema ligado, com preview do delta antes de escrever, marcando cada item no momento em que ele vai para que uma interrupcao seja retomavel sem reenviar o que ja foi.
append-requirement event: When o sistema de destino responde limite de taxa, the system shall recuar progressivamente e retomar, sem descartar item do lote.
append-requirement unwanted: The system shall not travar um lote por causa de um artefato em conflito: o artefato sai do lote com o motivo registrado e o restante segue.
append-criterion [unverified] Empurrar o mesmo ciclo duas vezes nao duplica no destino, interromper e repetir continua de onde parou, artefato em conflito sai do lote sem travar o resto, e limite de taxa nao perde item — verified by `backend/tests/test_integrations_bulk.py`.
bump-version minor
```
