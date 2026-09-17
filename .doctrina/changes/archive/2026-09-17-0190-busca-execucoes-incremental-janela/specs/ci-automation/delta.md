# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version minor
append-requirement event: When a busca de execuções é pedida, the system shall varrer apenas os intervalos da janela pedida que ainda não constam como cobertos, e registrar a cobertura por origem depois de varrer cada intervalo até o fim.
append-requirement event: When a busca é pedida com reconferência explícita, the system shall ignorar a cobertura registrada e varrer a janela inteira, sem apagar nem rebaixar o que já está no disco.
append-requirement state: While a janela pedida já estiver inteiramente coberta, the system shall dizer que reaproveitou o período em vez de devolver um resultado vazio indistinguível de "não há execução nova".
append-requirement unwanted: The system shall not registrar cobertura de um intervalo cuja varredura parou antes do fim, nem incluir na cobertura as últimas horas, porque uma execução longa conclui depois da varredura que a procuraria e o filtro do provedor é pela data de criação.
append-requirement unwanted: The system shall not interromper a paginação ao encontrar uma página inteiramente já ingerida; quem decide a parada é a data, e parar pela página torna o passado mais antigo inalcançável.
append-criterion [verified] A segunda busca do mesmo período lista uma janela de dois dias em vez de trinta e não rebaixa artifact; ampliar de 30 para 90 dias varre só os 60 que faltam; a borda recente é sempre reconferida; uma execução antiga fora da última página deixa de ser inalcançável; reconferir varre sem apagar; e uma parada no meio não registra cobertura — verified by `backend/tests/test_busca_incremental.py`.
```
