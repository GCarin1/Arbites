# Change 0026-automacao-selecao-de-arquivo-feature-tag-no-run — automacao: selecao de arquivo .feature + tag no run local (comando behave montado na UI), terminal ao vivo ja existente, acesso a artefatos (logs/screenshots/analise) do repo do target, editor visual do .env com catalogo de variaveis descritas, e disparo remoto GitHub Actions com feature/tag/ambiente/navegador/repositorio

- **Status:** proposed
- **Date:** 2026-07-09
- **Owner:**
- **Affects specs:** local-automation

## Why

automacao: selecao de arquivo .feature + tag no run local (comando behave montado na UI), terminal ao vivo ja existente, acesso a artefatos (logs/screenshots/analise) do repo do target, editor visual do .env com catalogo de variaveis descritas, e disparo remoto GitHub Actions com feature/tag/ambiente/navegador/repositorio

## What

- **runner.py** — `RunInfo/submit` aceitam `feature`; comando vira
  `behave [-f json…] [--tags=…] [<arquivo>.feature]` (tags opcionais quando o
  feature é dado).
- **api.py** — `LocalRunIn.feature` (resolve CTs pelos cenários do arquivo);
  `GET /targets/{name}/features` (arquivos+tags p/ dropdowns);
  `GET /targets/{name}/artifacts[/file]` (./logs, ./screenshots, ./analise, com
  guarda de traversal); `GET/PUT /targets/{name}/env` (preserva comentários e
  linhas desconhecidas) + `GET /env/catalog` (catálogo §1.5.1 e5 com descrições);
  `CIRunIn` ganha feature/environment/browser/source_repo → inputs do dispatch.
- **Frontend (Automation.tsx)** — run local com dropdown de .feature, tag com
  autocomplete (datalist) e preview do comando; card de **Artefatos** (download);
  card **Configuração local (.env)** agrupado por seção com descrição por campo;
  CI com Ambiente (dev|cer|prd), Navegador, .feature e Repositório de origem.
- **Testes** — `test_automation_flow.py` (3) + `test_ci_runs.py` (+1 inputs).

## Scope boundaries

- "Selecionar diretório" = o `local_path` do target (arbites.yaml), como já era;
  a seleção fina passa a ser por arquivo .feature/tag na UI.
- Terminal ao vivo (SSE) já existia — mantido.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest + build).
- [x] local-automation 7/7 e ci-automation 4/4 no `doctrina coverage`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
