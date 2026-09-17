# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version patch
append-requirement ubiquitous: The system shall calcular taxa de sucesso e contagem de falhas apenas sobre execuções que deram veredito sobre o produto — concluída com sucesso, com falha, ou por estouro de tempo —, e apresentar junto do número o denominador e quantas ficaram de fora.
append-requirement unwanted: The system shall not contar execução cancelada ou pulada como falha, nem responder 0% num período em que nenhuma execução deu veredito; zero afirma que tudo quebrou, e a verdade é que nada foi medido.
append-criterion [verified] A taxa é calculada sobre as conclusivas (25 de 32, não de 45), estouro de tempo conta como falha, cancelada e pulada ficam fora do denominador e aparecem nomeadas ao lado, um período só de canceladas responde ausência em vez de zero, e a contagem de falhas por repositório deixa de somar o que não falhou — verified by `backend/tests/test_execucao_conclusiva.py`.
```
