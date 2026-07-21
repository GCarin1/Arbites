# Spec — local-automation

**Capability:** local-automation
**Status:** active
**Implementation:** verified — M3 + reformulação §1.5.1 (feature+tag, artefatos, .env) (backend/arbites/runner.py, backend/arbites/gherkin_scan.py, backend/arbites/behave_json.py, frontend/src/components/Automation.tsx)
**Realizes:** SC5
**Last updated:** 2026-07-21
**Version:** 0.8.0

## Purpose

Executa a automação (Behave) localmente via subprocess, com log ao vivo por
SSE, fila por target e coleta do JSON do Behave para popular a execution —
mesmo modelo de dados da execução manual. O repo de automação é separado e
read-only; o elo é a tag `@CT-XXXX` no cenário.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /targets`, `POST /targets/{name}/scan`,
  `POST /runs/local`, `GET /runs/{exec_id}/stream` (SSE),
  `POST /runs/{exec_id}/cancel`.
- The system shall montar o comando Behave com `-f json -o {tmp}/result.json
  -f plain --tags=...` sobre o `local_path` do target, executando via
  `asyncio.create_subprocess_exec`.
- The system shall criar uma execution `origin: local_run` para cada run e
  popular `results[]` a partir do parse do JSON do Behave.
- The system shall injetar `ARBITES_EVIDENCE_DIR` no ambiente do
  subprocess; evidências capturadas pelos hooks do Behave são movidas para
  `evidences/` e hasheadas.
- The system shall permitir configurar working directory e `python_path`
  (virtualenv) por target.
- The system shall documentar o snippet de `environment.py` (contrato de
  evidências) para o usuário adicionar ao repo de automação.
- The system shall isolar o parser do JSON do Behave atrás de uma
  interface de adapter, com testes de contrato sobre JSONs de exemplo
  versionados.

- The system shall expor `GET /targets/{name}/features` (arquivos .feature e
  tags do target) para os dropdowns do run, e aceitar `feature` opcional em
  `POST /runs/local` (argumento posicional do behave). A lista vem do
  DISCO — mesma fonte do preview `GET /automation/browse-features` — e não
  só dos cenários já tagueados no índice, anotando por arquivo quantos
  cenários estão de fato mapeados a um CT (`mapped`) do total (`scenarios`).
- The system shall derivar do prefixo de CT CONFIGURADO
  (`id_prefixes.testcase`) tanto a regex de tag de cenário do scan
  (`gherkin_scan`) quanto o parser de resultado do Behave
  (`behave_json.parse_behave_json`, usado no run local e na coleta de CI) —
  nenhum dos dois hardcoda `CT-`.
- The system shall listar e servir artefatos pós-execução do target
  (`./logs`, `./screenshots`, `./analise`) via
  `GET /targets/{name}/artifacts[/file]`, com guarda de path traversal.
- The system shall expor edição visual do `.env` do target
  (`GET/PUT /targets/{name}/env` + `GET /env/catalog`), preservando
  comentários e linhas desconhecidas no PUT.
- The system shall expor `PUT /targets`, substituindo `automation_targets`
  no `arbites.yaml` por inteiro (mesmo padrão de `PUT /ai/providers`) —
  cadastro de target não exige editar o YAML manualmente.
- The system shall expor `GET /automation/browse-features` que escaneia
  `local_path` em busca de arquivos `.feature` (sem exigir que o target já
  exista/esteja salvo) e devolve caminho relativo + contagem de cenários de
  cada um, para o usuário escolher em vez de digitar um glob às cegas.

- The system shall permitir vincular cenários de .feature a CTs pelo NOME
  do cenário (`automation.feature_path` + `scenario_name`), sem escrever
  nada no repositório de automação (ADR 0003 preservado): `GET
  /automation/features-sync?target=` classifica cada cenário
  (linked_tag/linked/modified/new) e lista vínculos quebrados
  (rename/remoção); `POST /automation/features-sync/apply` cria CTs com os
  steps verbatim, re-baseia body de `modified` e re-vincula quebrados —
  só o que o usuário selecionou no modal, nunca automático.
- The system shall aceitar 1..N arquivos .feature em `POST /runs/local`
  (`features: list`), criando UMA execution com todos os CTs lastreados
  (por tag ou por nome); o parse do resultado casa cenário→CT também por
  nome (`name_map`).
- The system shall expor `GET /runs/active` (runs queued/running), e o menu
  lateral shall exibir um indicador pulsante no item Automação enquanto
  houver run ativo.
- The system shall definir `PYTHONIOENCODING=utf-8` no ambiente do
  subprocess do Behave — sem isso, no Windows o stream sai no encoding do
  console e acentos viram mojibake (quebrando terminal ao vivo e o parse
  de progresso).

### Event-driven

- When um run é solicitado para um target já em execução, the system shall
  enfileirá-lo em FIFO por target, com a fila visível na UI.
- When o subprocess emite stdout, the system shall transmiti-lo à UI via
  SSE em tempo real.
- When o timeout do target expira (default 30 min, configurável), the
  system shall marcar os resultados pendentes como `blocked` com
  `error: "timeout"` e encerrar o subprocess.
- When o run termina, the system shall parsear o JSON do Behave e popular
  os `results[]` com steps Gherkin e evidências.
- When o usuário aplica "update" (re-base de steps) na sync de features,
  the system shall marcar o CT com `needs_rerun: true` no frontmatter; when
  um resultado novo do CT é registrado numa execution posterior (manual,
  local ou CI), the system shall limpar o flag automaticamente.
- When o usuário salva a configuração de targets pela UI, the system shall
  reescanear cada target salvo (mesmo comportamento de `POST
  /targets/{name}/scan`), populando cenários/warnings imediatamente.
- When o usuário roda um `.feature` inteiro cujos cenários não têm tag de
  CT, the system shall executar o arquivo mesmo assim (execution criada sem
  CTs vinculados), em vez de recusar com `422 empty_selection` — o vínculo
  por tag é o caminho para rastreabilidade, não um pré-requisito para
  executar.

- When um run é disparado pela UI, the system shall oferecer em modal ir à
  execution criada ("ver andamento"); when o run termina, the system shall
  exibir toast de sucesso/erro.
- When o behave emite progresso (stream plain, EN/PT), the system shall
  persistir resultados parciais por cenário concluído (best-effort), com o
  Cucumber JSON final SEMPRE reconciliando o estado oficial.

### State-driven

- While um run está ativo em um target, the system shall manter lock por
  target (uma execução local por vez por target).
- While uma aba está sem dados (sem target configurado, sem run
  disparado), the system shall exibir um empty state com a instrução do
  próximo passo e um atalho para a aba correspondente.

### Unwanted-behavior (must-not)

- The system shall not escrever no repositório de automação.
- The system shall not gerenciar dependências do repo de automação
  (virtualenv é responsabilidade do usuário).
- The system shall not misturar controles de setup (targets/.env/token) com
  controles de operação (disparo/terminal) no mesmo bloco visual — a tela
  de Automação separa, NA ORDEM, Histórico (primeira e default;
  observabilidade: runs recentes com status + resumo por repositório com
  runs/falhas/MTTR/última execução, via `GET /executions?origin=` e
  `GET /metrics/automation`), Executar (operação) e Configurar (última;
  sem auto-troca de aba — o empty state do Histórico orienta o primeiro
  uso).
- The system shall not quebrar o repo de automação standalone: sem
  `ARBITES_EVIDENCE_DIR`, os hooks não fazem nada.
- The system shall not usar fontes divergentes para o preview de features e
  para a operação (dropdown/run) da mesma lista — o que o browse mostra é
  o que o dropdown oferece.

### Optional

- Where a variável `ARBITES_EVIDENCE_DIR` está setada e um step falha, the
  system may receber screenshots capturados pelo hook `after_step`.

## Acceptance criteria

1. [verified] Disparar automação real pela UI mostra log ao vivo e
   popula a execution com steps Gherkin — verified by
   `backend/tests/test_local_runs.py`.
2. [verified] Dois runs no mesmo target entram em fila FIFO — verified
   by `backend/tests/test_local_runs.py`.
3. [verified] Timeout marca pendentes como `blocked` com
   `error: "timeout"` — verified by `backend/tests/test_local_runs.py`.
4. [verified] Screenshot de falha do hook aparece hasheado em
   `evidences/` — verified by `backend/tests/test_local_runs.py`.

5. [verified] Features e tags do target expostos p/ seleção; run aceita
   feature específico — verified by `backend/tests/test_automation_flow.py`.
6. [verified] Artefatos listados e baixáveis com traversal bloqueado —
   verified by `backend/tests/test_automation_flow.py`.
7. [verified] `.env` editável por chave com comentários preservados e
   catálogo com descrições — verified by `backend/tests/test_automation_flow.py`.

8. [verified] Salvar um target pela UI persiste em `arbites.yaml`, aparece
   em `GET /targets` com a contagem de cenários já escaneada, e um target
   com `local_path` inexistente não derruba a rota — verified by
   `backend/tests/test_automation_targets_config.py`.

9. [verified] `GET /automation/browse-features` lista os `.feature`
   encontrados (caminho relativo + nº de cenários) para um `local_path`
   arbitrário, mesmo sem target salvo; caminho inexistente é rejeitado
   (422) — verified by `backend/tests/test_automation_targets_config.py`.

10. [verified] Target salvo apontando para um repositório de features SEM
    tags de CT: o dropdown lista o arquivo (com `mapped: 0`) e rodar o
    arquivo inteiro cria a execution (201, sem CTs vinculados) e dispara o
    behave de verdade — verified by
    `backend/tests/test_gherkin.py` e `backend/tests/test_local_runs.py`.

11. [verified] Com `id_prefixes.testcase` customizado, cenários tagueados
    com o prefixo configurado são mapeados pelo scan E pelo parser de
    resultado do Behave (run local e coleta de CI) — verified by
    `backend/tests/test_gherkin.py` e `backend/tests/test_behave_json.py`.

12. [verified] A tela de Automação separa Configurar/Executar/Histórico; o
    Histórico lista runs recentes (local + CI, via `origin=`) com status e
    o resumo por repositório (runs/falhas/MTTR/última execução) vem de
    `GET /metrics/automation`; abas sem dados mostram instrução do próximo
    passo — verified by build + smoke dos endpoints consumidos
    (`GET /executions?origin=`, `GET /metrics/automation`) + revisão visual
    (endpoints já cobertos por `backend/tests/test_executions.py` e
    `backend/tests/test_automation_report.py`).

13. [verified] Sync por nome: vincular cria CT verbatim; editar steps vira
    `modified` e o update re-baseia; rename vira vínculo quebrado e o
    relink conserta; CT por nome entra no run do arquivo — verified by
    `backend/tests/test_feature_sync.py` (5 testes).
14. [verified] Run com N features cria 1 execution com todos os CTs;
    `/runs/active` reflete o run e esvazia ao fim; progresso parcial
    aparece no stream e o JSON final reconcilia (behave real) — verified
    by `backend/tests/test_local_runs.py`.
15. [verified] Apply de update marca `needs_rerun` no CT e um resultado
    novo do CT limpa o flag — verified by
    `backend/tests/test_feature_sync.py`
    (`test_update_marks_needs_rerun_and_new_result_clears_it`).

## Maturity

**MVP (committed):**

- Runs locais Behave com SSE, fila, timeout, parse JSON, evidências via
  hooks; cadastro de targets pela UI (sem editar `arbites.yaml` na mão) com
  descoberta de `.feature` por scan do repositório; rodar um `.feature`
  inteiro funciona mesmo sem nenhum cenário tagueado a um CT; tela em 3
  abas (Configurar/Executar/Histórico) com resumo operacional e empty
  states instrutivos.

**Future (aspirational, not committed):**

- Outros runners além do Behave via a mesma interface de adapter
  (princípio "adaptadores, não integrações exclusivas").
- Agente de execução separado (apenas quando houver execução remota
  própria — ADR do intake).

## Out of scope for this spec

- Execução via GitHub Actions (ver `ci-automation`).
- Parsing/scan de features (ver `indexing`).
