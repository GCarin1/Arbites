---
name: default-por-tipo-de-provider
description: Fallback único (ex.: base_url → OpenAI) para vários tipos rota provider local para a nuvem quando o campo é omitido — use default por tipo.
when: Ao dar valor default a um campo opcional (base_url, host, porta, região) que varia por tipo/kind de integração — especialmente providers de LLM locais (LM Studio/Ollama/vLLM).
---

# Skill — default-por-tipo-de-provider

## When to use this skill

- Está escrevendo um `build_*`/factory que aceita `kind` + campos opcionais e
  aplica um default quando o campo vem vazio.
- Há tipos "locais" (LM Studio, Ollama, vLLM) e "nuvem" (OpenAI, Anthropic)
  compartilhando o mesmo caminho.

## O bug (real, build_provider)

`base = config.get("base_url") or "https://api.openai.com/v1"` valia para TODOS
os kinds OpenAI-compatíveis. Se o usuário escolhia `lmstudio`/`ollama`/`vllm` e
**omitia** a base_url (achando que o tipo já implicava localhost), o modelo
local era **silenciosamente roteado para o OpenAI** — falha confusa (401/erro
de rede) sem pista da causa.

## Procedure

1. Default **por tipo**, não um fallback único:
   ```python
   _DEFAULT_BASE_URL = {
       "lmstudio": "http://localhost:1234/v1",
       "ollama":   "http://localhost:11434/v1",
       "vllm":     "http://localhost:8000/v1",
   }
   base = config.get("base_url") or _DEFAULT_BASE_URL.get(kind, "https://api.openai.com/v1")
   ```
2. Valor explícito do usuário sempre prevalece sobre o default.
3. Teste cada tipo local (default correto) + o tipo nuvem (mantém o default de
   nuvem) + override explícito.

## Anti-patterns

- Um único `or "<url da nuvem>"` cobrindo tipos locais e remotos.
- Assumir que "o usuário vai preencher a URL" para endpoints locais — o campo
  costuma estar marcado como "(opcional)".

## Related material

- `backend/arbites/ai.py` — `build_provider`, `_DEFAULT_BASE_URL`.
- `backend/tests/test_ai_optional.py::test_local_provider_kinds_default_to_localhost_not_openai`.
