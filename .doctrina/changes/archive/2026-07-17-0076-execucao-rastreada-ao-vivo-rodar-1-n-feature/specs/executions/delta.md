# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

Progresso incremental ([unverified] até implementar):

### Ubiquitous
- The system shall aceitar atualizações incrementais de resultado durante
  um run automatizado (por cenário concluído), persistidas na execution
  antes do fim do run — o estado final oficial vem da reconciliação com o
  JSON do Behave.

### Acceptance criteria (a acrescentar)
- [unverified] Durante um run em andamento a execution já mostra
  resultados parciais; ao final o estado bate com o JSON — verified by
  teste com behave real.
