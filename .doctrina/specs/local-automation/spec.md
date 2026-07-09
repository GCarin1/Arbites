# Spec — local-automation

**Capability:** local-automation
**Status:** active
**Implementation:** verified — M3 + reformulação §1.5.1 (feature+tag, artefatos, .env) (backend/arbites/runner.py, backend/arbites/gherkin_scan.py, backend/arbites/behave_json.py, frontend/src/components/Automation.tsx)
**Realizes:** SC5
**Last updated:** 2026-07-09
**Version:** 0.3.0

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
  `POST /runs/local` (argumento posicional do behave).
- The system shall listar e servir artefatos pós-execução do target
  (`./logs`, `./screenshots`, `./analise`) via
  `GET /targets/{name}/artifacts[/file]`, com guarda de path traversal.
- The system shall expor edição visual do `.env` do target
  (`GET/PUT /targets/{name}/env` + `GET /env/catalog`), preservando
  comentários e linhas desconhecidas no PUT.

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

### State-driven

- While um run está ativo em um target, the system shall manter lock por
  target (uma execução local por vez por target).

### Unwanted-behavior (must-not)

- The system shall not escrever no repositório de automação.
- The system shall not gerenciar dependências do repo de automação
  (virtualenv é responsabilidade do usuário).
- The system shall not quebrar o repo de automação standalone: sem
  `ARBITES_EVIDENCE_DIR`, os hooks não fazem nada.

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

## Maturity

**MVP (committed):**

- Runs locais Behave com SSE, fila, timeout, parse JSON, evidências via
  hooks.

**Future (aspirational, not committed):**

- Outros runners além do Behave via a mesma interface de adapter
  (princípio "adaptadores, não integrações exclusivas").
- Agente de execução separado (apenas quando houver execução remota
  própria — ADR do intake).

## Out of scope for this spec

- Execução via GitHub Actions (ver `ci-automation`).
- Parsing/scan de features (ver `indexing`).
