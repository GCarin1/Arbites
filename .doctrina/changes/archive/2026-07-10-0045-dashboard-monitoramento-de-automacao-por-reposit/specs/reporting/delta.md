# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /metrics/automation` que agrega as execuções de
  automação (`origin != manual`) do período, agrupadas por REPOSITÓRIO
  extraído do NOME da execução via regex configurável
  (`ci_monitoring.name_pattern` no `arbites.yaml`, com grupos nomeados `repo`
  obrigatório e `env` opcional; default genérico, sem referência a
  empresa/projeto), com o desfecho de cada run (passed/failed/…) derivado dos
  seus `results[]`.
- The system shall ordenar os repositórios do relatório de automação
  pior-primeiro (mais falhas, depois maior taxa de falha), reportar
  passed/failed/pass_rate por repo e por ambiente, e contar em `unparsed` os
  runs cujo nome não casa o padrão (sinal de padrão a ajustar).

### Unwanted-behavior (must-not)

- The system shall not derrubar `GET /metrics/automation` quando a regex
  configurada é inválida; deve cair no padrão default e reportar
  `pattern_error`.
- The system shall not referenciar nenhuma empresa/organização/projeto
  específico no padrão default nem na spec (o padrão é genérico e
  sobrescrevível).

## Acceptance criteria

8. [verified] `GET /metrics/automation` agrupa runs de automação por repo
   (pior-primeiro), deriva passed/failed por run dos resultados, ignora
   execuções manuais, conta `unparsed` e respeita um `name_pattern`
   customizado; regex inválida não derruba a rota (reporta `pattern_error`)
   — verified by `backend/tests/test_automation_report.py`.
