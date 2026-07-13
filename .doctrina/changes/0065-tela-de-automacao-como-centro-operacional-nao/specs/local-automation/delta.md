# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

Note: a mudança é majoritariamente de UI, mas a tela de Automação é a
superfície desta capability (junto com `ci-automation` para o disparo
remoto — o delta fica aqui por ser a tela única; o disparo GitHub não muda
de contrato).

---

Tela de Automação como centro operacional — requisitos a acrescentar
(todos [unverified] até implementar):

### Ubiquitous

- The system shall organizar a tela de Automação em 3 abas com papéis
  distintos: Configurar (targets, .env, token — setup), Executar (disparo
  local e remoto + terminal ao vivo — operação) e Histórico (runs recentes
  — observabilidade).
- The system shall exibir no Histórico os últimos runs de automação com
  status, duração e origem, mais o resumo tempo médio/falhas/última
  execução, reutilizando os dados de execuções `origin != manual` e o
  `automation_report` (com o `ci_monitoring.name_pattern` configurado).
- The system shall exibir, em cada aba vazia, um empty state com a
  instrução do próximo passo (sem target → como configurar; sem run → como
  executar o primeiro).

### Unwanted-behavior (must-not)

- The system shall not misturar controles de setup (targets/env/token) com
  controles de operação (disparo/terminal) no mesmo bloco visual.

### Acceptance criteria (a acrescentar)

- [unverified] A tela separa Configurar/Executar/Histórico; o Histórico
  lista runs recentes com status/duração e o resumo (tempo médio, falhas,
  última execução) bate com `automation_report` — verified by teste de API
  do agregado + revisão visual documentada.
- [unverified] Cada aba sem dados mostra instrução útil do próximo passo —
  verified by revisão visual documentada.

### Maturity → MVP (acrescentar)

- Tela em 3 abas (Configurar/Executar/Histórico) com resumo operacional e
  empty states instrutivos.
