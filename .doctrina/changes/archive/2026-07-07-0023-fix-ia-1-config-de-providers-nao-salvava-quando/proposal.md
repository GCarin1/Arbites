# Change 0023-fix-ia-1-config-de-providers-nao-salvava-quando — fix IA: (1) config de providers nao salvava quando o usuario preenchia o formulario e clicava Salvar sem 'Adicionar a lista' — Salvar passa a incluir o provider/chave pendente; (2) kind local (lmstudio/ollama/vllm) sem base_url caia no OpenAI — default de base_url por tipo

- **Status:** applied
- **Applied:** 2026-07-07
- **Date:** 2026-07-07
- **Owner:**
- **Affects specs:** (none — chore)

## Why

fix IA: (1) config de providers nao salvava quando o usuario preenchia o formulario e clicava Salvar sem 'Adicionar a lista' — Salvar passa a incluir o provider/chave pendente; (2) kind local (lmstudio/ollama/vllm) sem base_url caia no OpenAI — default de base_url por tipo

## What

- **Bug 1 (frontend, config não salva)** — `AiAssist.tsx` `ProvidersCard.save()`
  agora inclui o provider (e a chave) digitado no formulário mesmo sem clicar
  "Adicionar à lista", e define-o como padrão se não houver. Antes, preencher o
  form e clicar "Salvar configuração" não persistia nada (o item só entrava no
  payload via "Adicionar à lista"). + legenda esclarecendo o fluxo.
- **Bug 2 (backend, misroute)** — `ai.build_provider`: `_DEFAULT_BASE_URL` por
  tipo. `lmstudio`→localhost:1234, `ollama`→11434, `vllm`→8000; só openai/
  openai_compatible/openrouter mantêm o default OpenAI. Antes, qualquer kind
  local sem base_url caía em `api.openai.com` (modelo local roteado p/ nuvem).
  Valor explícito sempre prevalece. Teste em `test_ai_optional.py`.

## Verificação do base_url em todos os usos de IA

Confirmado: os 5 pontos que usam IA (generate-testcases, review, negative-cases,
daily generate, meeting summarize) passam por `_ai_provider` → `build_provider`,
que usa o `base_url` configurado do provider. Não há URL hardcoded no caminho —
o único `api.openai.com` é o default de fallback. Round-trip PUT/GET de config
persiste em `arbites.yaml` e lê de volta (keyring do SO funciona no Windows).

## Scope boundaries

- Bug 1 é UI-only; Bug 2 é backend com teste.
- Sem mudança de spec (comportamento já previsto: "base URL configurável cobrindo
  LM Studio/Ollama/vLLM").

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 93 + build do frontend).
- [x] Bug 2 coberto por `test_ai_optional.py::test_local_provider_kinds_default_to_localhost_not_openai`.
- [x] base_url confirmado sem hardcode nos 5 usos de IA (round-trip PUT/GET persiste).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
