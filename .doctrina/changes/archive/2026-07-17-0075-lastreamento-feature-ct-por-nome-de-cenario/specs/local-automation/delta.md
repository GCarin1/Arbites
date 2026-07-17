# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

Lastreamento por nome ([unverified] até implementar):

### Ubiquitous
- The system shall permitir vincular cenários de .feature a CTs pelo NOME
  do cenário (`automation.feature_path` + `scenario_name`), sem escrever
  nada no repositório de automação (ADR 0003 preservado).
- The system shall expor `POST /automation/link-features` (cria CTs
  automated a partir da seleção do modal: título = nome do cenário, body =
  steps verbatim) e `GET /automation/sync-status?target=` (classifica:
  feature novo, cenário novo, steps modificados, vínculo quebrado por
  rename/remoção).
- The system shall registrar vínculos por nome também no scan/índice
  (tabela `scenarios`; schema descartável, ADR 0001).

### Event-driven
- When o usuário clica "Buscar .feature" num target salvo, the system shall
  abrir o modal de sync com o estado de cada feature/cenário e permitir
  escolher o que criar / atualizar body / re-vincular / ignorar.

### Acceptance criteria (a acrescentar)
- [unverified] Vincular cenários cria CTs com steps verbatim; re-rodar a
  sync após editar o .feature classifica novo/modificado/quebrado e as
  ações do modal aplicam — verified by testes de API do link/sync.
