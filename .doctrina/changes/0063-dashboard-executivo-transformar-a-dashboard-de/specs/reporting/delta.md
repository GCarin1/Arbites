# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

Dashboard executivo — requisitos a acrescentar (todos [unverified] até
implementar; a implementação desta change prova e flipa):

### Ubiquitous

- The system shall devolver, para cada métrica do summary, a comparação com
  o período imediatamente anterior de mesmo tamanho (`previous`, `delta`) —
  o usuário vê o que melhorou/piorou, não só o valor atual.
- The system shall exibir no Dashboard um bloco de alertas de risco derivado
  dos dados existentes (Health Score baixo, automação quebrada, defeitos
  críticos envelhecendo, CTs flaky), cada alerta navegando à seção de
  origem; reutiliza os achados `bad` do Agente Auditor (capability `audit`).
- The system shall exibir a última atualização dos dados
  (`last_reindex`) no Dashboard.
- The system shall exibir uma seção "top problemas" (piores repositórios de
  automação, CTs que mais falham, defeitos mais antigos) agregando os
  reports existentes num só lugar.
- The system shall exibir "ações recomendadas" derivadas por regras
  determinísticas dos dados (stories sem CT, repo quebrado há N dias,
  defeito antigo sem causa raiz) — nunca por IA nesta versão.

### Acceptance criteria (a acrescentar)

13. [unverified] O summary devolve `previous`/`delta` por métrica comparando
    janelas consecutivas de mesmo tamanho — verified by
    `backend/tests/test_metrics.py` (a escrever).
14. [unverified] O Dashboard exibe alertas de risco derivados dos achados
    do auditor + Health Score, "top problemas", "ações recomendadas" por
    regra e o timestamp do último reindex — verified by teste de API +
    revisão visual documentada.

### Maturity → MVP (acrescentar)

- Dashboard executivo: variação vs período anterior, alertas de risco,
  top problemas, ações recomendadas (por regra), última atualização.
