# Spec — risk-map

**Capability:** risk-map
**Status:** active
**Implementation:** verified
**Realizes:** n/a — capability nova (Mapa de Risco), fora do escopo do intake original; surgiu de uma sessão de brainstorm sobre memória/contexto para IA
**Last updated:** 2026-07-12
**Version:** 0.1.1

## Purpose

Aponta, dentro de um repositório de código local, os arquivos que mais
mudam (churn de git), os que mais quebram (commits cuja mensagem referencia
um defeito real já registrado no Arbites) e o quão testado está o
repositório como um todo (pass rate de automação), numa visualização estilo
heatmap do GitHub. O objetivo é dar sinal visual de onde o risco se
concentra sem exigir que ninguém cruze manualmente `git log`, a lista de
defeitos e o painel de automação.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /risk-map?days=` que escaneia cada
  repositório configurado em `arbites.yaml` (`risk_repos`: lista de
  `{name, local_path}`, mesma forma de `automation_targets` — mas uma lista
  separada, pois o repositório de automação e o repositório de código-fonte
  sob teste podem não ser o mesmo) via `git log` local (subprocess,
  read-only).
- The system shall calcular, por arquivo tocado nos commits da janela
  (`days`, default 90): `churn` (nº de commits que tocaram o arquivo) e
  `defect_commits` (nº de commits, dentre esses, cuja mensagem referencia
  um ID de defeito que existe de fato no índice do Arbites — a regex usa o
  prefixo CONFIGURADO em `id_prefixes.defect`, não `DF-` fixo).
- The system shall devolver, por repositório configurado, o pass rate de
  automação (reaproveitando `metrics.automation_report`, computado uma
  única vez por requisição e com o mesmo `ci_monitoring.name_pattern`
  configurado do relatório de automação, casado pelo nome do repo) como
  sinal de "testado menos", junto com o total de commits e a lista de
  arquivos (ordenada por churn, pior-primeiro, limitada a um topo N).

### Event-driven

- When um commit menciona um ID de defeito que NÃO existe no índice do
  Arbites, the system shall ignorar a menção (não conta como
  `defect_commits`) — evita falso positivo de uma string parecida com
  `DF-123` que não é de fato um defeito rastreado.

### Unwanted-behavior (must-not)

- The system shall not derrubar a rota quando um `local_path` configurado
  não existe ou não é um repositório git válido — devolve esse repositório
  com um campo `error` explicativo e listas vazias, os demais repositórios
  configurados seguem sendo escaneados normalmente.
- The system shall not escrever nada no repositório do usuário — todo
  acesso a git é read-only (`git log`).
- The system shall not referenciar nenhuma empresa/organização/projeto
  específico nos defaults ou na spec desta capability.

### Optional

- Where nenhum `risk_repos` está configurado, the system may devolver uma
  lista vazia de repositórios (sem erro) — a feature é opt-in.

## Acceptance criteria

1. [verified] `GET /risk-map` ranqueia os arquivos de um repo configurado
   por churn (nº de commits na janela), pior-primeiro — verified by
   `backend/tests/test_risk_map.py`.
2. [verified] Um commit cuja mensagem referencia um DF-ID que existe no
   índice soma 1 a `defect_commits` de cada arquivo que ele tocou; um DF-ID
   que não existe é ignorado — verified by `backend/tests/test_risk_map.py`.
3. [verified] `local_path` inexistente ou inválido devolve `error`
   preenchido e listas vazias para aquele repo, sem derrubar a rota —
   verified by `backend/tests/test_risk_map.py`.
4. [verified] O pass rate de automação do repo é exposto quando o nome do
   repo em `risk_repos` casa com um repo já detectado por
   `automation_report`, e fica `null` quando não há runs correspondentes —
   verified by `backend/tests/test_risk_map.py`.
5. [verified] Sem nenhum `risk_repos` configurado, a rota devolve uma lista
   vazia de repositórios — verified by `backend/tests/test_risk_map.py`.
6. [verified] Com `ci_monitoring.name_pattern` customizado o pass rate do
   repo continua sendo calculado, e com `id_prefixes.defect` customizado a
   correlação commit↔defeito usa o prefixo configurado — verified by
   `backend/tests/test_risk_map.py`.

## Maturity

**MVP (committed):**

- Churn por arquivo via `git log` local, cruzamento com defeitos reais via
  menção ao ID (prefixo configurável) na mensagem do commit, pass rate de
  automação por repo (padrão de nome configurável), tolerância a
  repositório inválido/ausente, heatmap no Dashboard (grade de quadrados
  coloridos por churn, marcador para commits ligados a defeito).

**Future (aspirational, not committed):**

- Complexidade ciclomática/tamanho do arquivo como segundo eixo de risco
  (hoje é só churn).
- Correlação automática entre arquivo e squad/story (hoje não há
  vínculo entre caminho de arquivo e artefatos do Arbites além da menção a
  DF-ID no commit).

## Out of scope for this spec

- Escrita no repositório do usuário (branches, commits, tags) — todo acesso
  é read-only.
- Suporte a outros VCS além de git.
