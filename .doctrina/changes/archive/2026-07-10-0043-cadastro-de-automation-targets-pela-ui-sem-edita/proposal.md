# Change 0043-cadastro-de-automation-targets-pela-ui-sem-edita — cadastro de automation targets pela UI (sem editar arbites.yaml na mao): novo card em Automacao com formulario (nome, caminho, python, working dir, timeout, features_glob) e PUT /targets substituindo a lista inteira (mesmo padrao de PUT /ai/providers); ao digitar o caminho do repo, botao Buscar arquivos .feature chama novo GET /automation/browse-features que escaneia o filesystem e devolve a lista real para o usuario selecionar (inclusive restringir a um arquivo especifico), antes mesmo do target existir

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** local-automation

## Why

cadastro de automation targets pela UI (sem editar arbites.yaml na mao): novo card em Automacao com formulario (nome, caminho, python, working dir, timeout, features_glob) e PUT /targets substituindo a lista inteira (mesmo padrao de PUT /ai/providers); ao digitar o caminho do repo, botao Buscar arquivos .feature chama novo GET /automation/browse-features que escaneia o filesystem e devolve a lista real para o usuario selecionar (inclusive restringir a um arquivo especifico), antes mesmo do target existir

## What

O usuário não queria abrir `arbites.yaml` na mão pra cadastrar um target,
nem digitar `features_glob` às cegas — queria ver os `.feature` que existem
de verdade no repositório de automação e escolher.

- **backend/arbites/gherkin_scan.py** — `list_feature_files(local_path, glob)`:
  scan avulso (sem tocar em índice/DB), usável ANTES de o target existir.
- **backend/arbites/api.py** — `AutomationTargetIn`/`AutomationTargetsIn`;
  `PUT /targets` (substitui `automation_targets` por inteiro, mesmo padrão
  já usado em `PUT /ai/providers`, e reescaneia cada target ao salvar);
  `GET /automation/browse-features` (scan de um `local_path` arbitrário,
  422 se a pasta não existir); `GET /targets` passa a devolver também
  `python_path`/`working_dir`/`timeout_minutes` (necessários pro form de
  edição, antes só apareciam no YAML cru).
- **frontend/src/components/Automation.tsx** — `TargetsCard`: tabela
  editável (Editar/Remover/Re-scan) + formulário completo (nome, caminho,
  python venv, working dir, timeout, features_glob avançado) + botão
  "Buscar arquivos .feature" que chama o scan avulso e lista os arquivos
  encontrados com contagem de cenários — clicar num deles restringe
  `features_glob` a esse arquivo específico; "Usar todos" volta ao glob
  padrão. "Salvar configuração" faz `PUT /targets` de uma vez (mesmo padrão
  de staging + save do card de Providers de IA).

## Scope boundaries

- Não adiciona um seletor de pasta nativo (não é viável numa SPA web sem
  Electron/Tauri) — `local_path` continua sendo digitado; o "Buscar" dá o
  feedback imediato que substitui a necessidade de um browse nativo.
- Não altera o fluxo de RUN (`GET /targets/{name}/features`, já existente,
  continua servindo o dropdown de "qual feature rodar" para um target já
  salvo e escaneado) — esta change é sobre CADASTRAR o target.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (135 testes backend + build frontend).
- [x] Critérios #8 e #9 do local-automation citam
      `backend/tests/test_automation_targets_config.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
