# Change 0099-local-automation-correcoes-de-execucao-injetar-o — correções de execução da automação

- **Status:** applied
- **Applied:** 2026-07-21
- **Date:** 2026-07-21
- **Owner:**
- **Affects specs:** local-automation

## Why

Bugs reportados ao rodar automação pela ferramenta:

1. O browser abre mas não acessa o site e reabre em sequência: o runner
   monta o ambiente do subprocess a partir de `os.environ` e **nunca
   injeta o `.env` do projeto-alvo** — `BASE_URL`/`LOCAL_BROWSER`/etc.
   faltam, cada cenário abre um browser sem URL e a suíte "churna".
2. O catálogo de `.env` na UI é uma **lista fixa** (`ENV_CATALOG`) com
   campos de UM projeto específico — o Arbites deve se adaptar ao projeto,
   não impor campos padrão.
3. Os steps do terminal do run **somem ao trocar de aba** (estado local do
   componente), embora o servidor guarde `run.log` e o stream faça replay.
4. O `EXEC-XXXX` do run **não é navegável** para o board (kanban) dele.
5. Selecionar um `.feature` inteiro é pouco descoberto/robusto (lista vazia
   quando o `features_glob` não casa) — falta "selecionar todos".

## What

- **Backend (runner):** ao disparar o run, carregar o `.env` do
  `local_path` do target e **mesclar no ambiente do subprocess** (valores
  do projeto entram; `ARBITES_*`/`PYTHONIOENCODING` não são sobrescritos).
- **Backend (catálogo):** `GET /env/catalog` passa a **derivar** o catálogo
  do próprio projeto — chaves/seções/descrições lidas do `.env` e do
  `.env.example` do target — em vez do `ENV_CATALOG` fixo. Sem target ou
  sem arquivo, catálogo vazio (o usuário adiciona chaves livres).
- **Frontend (stream):** ao montar a aba Automação, **reconectar** ao run
  ativo (via `/runs/active`) e reabrir o `EventSource` (replay do buffer),
  restaurando o terminal.
- **Frontend (navegação):** o `Run EXEC-XXXX` do painel vira **link** que
  navega ao board da execution (`onNavigate`).
- **Frontend (seleção):** feature-picker com **"selecionar todos / limpar"**
  e mensagem clara quando a lista vem vazia (glob).

## Scope boundaries

- Não controla o tamanho/posição da janela do browser — isso é do código
  Selenium do projeto-alvo; o Arbites só garante que o `.env` chega.
- Não muda o contrato do run (`POST /runs/local`) nem o parser do Behave.
- `GET /env/catalog` passa a derivar do target (`?target=`); sem target
  útil, devolve catálogo vazio.

## Verification

- [x] `frontend-build` ✓ e todos os testes NOVOS/tocados do backend passam; o
  único vermelho da suíte é `test_timeout_marks_pending_as_blocked`, teste de
  timing pré-existente (falha idêntica na `develop`, alheio a este change).
- [x] A spec de local-automation tem os critérios novos citando evidência (`doctrina coverage`).
- [x] Run injeta o `.env` do target no subprocess; catálogo deriva do projeto — `backend/tests/test_local_runs.py` + `backend/tests/test_automation_targets_config.py`.
- [x] Stream reconecta ao voltar; EXEC navega ao board; selecionar-todos de features — build + revisão visual.

## Open questions

Nenhuma.
