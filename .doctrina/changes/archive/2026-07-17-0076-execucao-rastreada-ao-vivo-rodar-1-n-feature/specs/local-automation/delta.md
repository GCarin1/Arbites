# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

Execução rastreada ao vivo ([unverified] até implementar):

### Ubiquitous
- The system shall aceitar 1..N arquivos .feature em `POST /runs/local`
  (`features: list`), criando UMA execution com todos os CTs lastreados
  dos arquivos (por tag ou por nome).
- The system shall casar resultado→CT também por nome de cenário no parse
  do Behave (name_map do target), além da tag.
- The system shall expor `GET /runs/active` (runs queued/running) e o menu
  lateral shall exibir indicador pulsante no item Automação enquanto
  houver run ativo.

### Event-driven
- When um run é disparado, the system shall oferecer em modal ir à
  execution criada ("ver andamento"); when o run termina, the system shall
  exibir toast de sucesso/erro.
- When o behave emite progresso (plain stream), the system shall atualizar
  os resultados da execution por cenário concluído (best-effort, EN/PT),
  com o JSON final SEMPRE reconciliando o estado oficial.

### Acceptance criteria (a acrescentar)
- [unverified] Run com 2 features de arquivos diferentes cria 1 execution
  com todos os CTs; progresso incremental aparece antes do fim; o JSON
  final reconcilia; /runs/active reflete o run — verified by testes de
  API + behave real.
