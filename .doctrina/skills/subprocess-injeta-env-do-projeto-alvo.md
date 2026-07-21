---
name: subprocess-injeta-env-do-projeto-alvo
description: Ao rodar um projeto-alvo externo por subprocess (Behave/WebDriver/CLI), o Arbites deve carregar e injetar o `.env` do projeto no ambiente do processo filho — nunca assumir que o processo pai já tem as variáveis.
when: O agente vai criar/alterar um runner que dispara um processo externo (behave, pytest, node, etc.) sobre um projeto-alvo configurado por `local_path`, ou investigar por que a automação "abre o browser mas não faz nada".
---

# Skill — subprocess-injeta-env-do-projeto-alvo

## When to use this skill

- Vai mexer em `backend/arbites/runner.py` (ou qualquer código que monte o
  ambiente de um subprocess que roda o projeto-alvo).
- Está investigando um bug onde a automação inicia mas o browser/WebDriver
  não navega, reabre em sequência, ou "não faz o teste" — sintoma clássico
  de variáveis de ambiente ausentes (`BASE_URL`, `LOCAL_BROWSER`, credenciais).

## Procedure

1. **Carregue o `.env` do target** (`local_path/.env`) com um parser
   tolerante (`runner.load_env_file`) — ignora comentários/linhas em branco,
   remove `export ` e aspas; arquivo ausente → `{}` (best-effort, nunca
   derruba o run).
2. **Mescle no ambiente do subprocess** partindo de `os.environ`:
   `env = build_run_env(dict(os.environ), local_path, evidence_dir)`.
3. **Reafirme as chaves de controle do Arbites por último**
   (`ARBITES_EVIDENCE_DIR`, `PYTHONIOENCODING`) — o `.env` do projeto
   NUNCA pode sobrescrevê-las. A ordem (`env.update(dotenv)` e só então
   `env[...] = ...`) garante a precedência.
4. **Teste sem depender do subprocess real:** o env-building é um helper puro
   (`build_run_env`) — cubra injeção + precedência em
   `backend/tests/test_local_runs.py`.

## Anti-patterns

- Montar `env = dict(os.environ)` e passar ao subprocess **sem** injetar o
  `.env` do projeto — o teste roda "no vazio": browser abre sem URL, cada
  cenário reabre um browser e a suíte churna. Foi o bug do change 0099.
- Exigir que o usuário exporte as variáveis manualmente no shell do Arbites —
  o Arbites se adapta ao projeto, não o contrário.
- Deixar o `.env` do projeto sobrescrever `ARBITES_*`/`PYTHONIOENCODING`
  (quebra evidências e o encoding do stream ao vivo).

## Related material

- `backend/arbites/runner.py` — `load_env_file`, `build_run_env`, `_execute`.
- `.doctrina/specs/local-automation/spec.md` — o contrato de execução.
