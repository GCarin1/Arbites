# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version minor
append-requirement event: When um relatório de cenários é lido, the system shall guardar a mensagem do passo que falhou, para que a pergunta "por que falhou" seja respondida sem abrir a execução.
append-requirement event: When o diagnóstico do período é pedido, the system shall responder quais cenários mais falharam, quais nunca falharam, quais mensagens de erro mais se repetem agrupadas pelo molde, e quais etapas do pipeline mais quebram, com recorte por repositório.
append-requirement unwanted: The system shall not agrupar mensagens de erro pelo texto cru nem listar como estável um cenário sem histórico; o primeiro devolve uma lista de linhas únicas e o segundo dá um atestado que ninguém provou.
append-criterion [verified] A mensagem do passo que falhou é lida e guardada só na primeira linha; mensagens iguais com números, tempos ou endereços diferentes caem no mesmo molde; o diagnóstico responde o cenário que mais falhou, os que nunca falharam com pelo menos três execuções, o erro mais repetido e a etapa que mais quebra; e o filtro por repositório recorta de verdade — verified by `backend/tests/test_diagnostico_observabilidade.py`.
```
