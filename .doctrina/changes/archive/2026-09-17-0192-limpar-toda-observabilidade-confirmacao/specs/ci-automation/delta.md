# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version minor
append-requirement event: When a limpeza total da observabilidade é pedida, the system shall responder antes quantas execuções, quantos anexos, quanto espaço e que intervalo de datas seriam removidos, para que a confirmação seja informada.
append-requirement event: When a limpeza total é confirmada, the system shall mover execuções e anexos para a lixeira, esquecer a cobertura de busca junto, e preservar as origens declaradas.
append-requirement unwanted: The system shall not apagar a observabilidade fora da lixeira nem executar a limpeza total para quem não administra a instância.
append-criterion [verified] A prévia informa execuções, anexos, bytes e intervalo sem remover nada; a limpeza manda tudo para a lixeira e o índice esquece junto; a cobertura de busca é descartada com o dado; as origens declaradas permanecem; e quem não é admin recebe recusa — verified by `backend/tests/test_limpar_observabilidade.py`.
```
