---
name: modelo-de-raciocinio-content-vazio
description: Modelos de raciocínio (glm-4.7-flash, qwen-thinking) via LM Studio devolvem o pensamento em reasoning_content e podem deixar content vazio; timeouts curtos os matam no meio e prompts ambíguos os fazem entrar em loop.
when: Ao integrar um modelo de raciocínio local para saída estruturada e a resposta vier com content="" , finish_reason=stop, reasoning_content enorme/repetido, ou o cliente desconectar por timeout (~120s) enquanto o modelo ainda pensa.
---

# Skill — modelo-de-raciocinio-content-vazio

## When to use this skill

- Provider é um modelo *de raciocínio* local (glm-4.x-flash, qwen-*-thinking)
  via LM Studio/Ollama e o import/geração falha "sem JSON".
- Log típico: `content: ""`, `finish_reason: "stop"`, `reasoning_content` com
  milhares de tokens repetindo a mesma frase ("Let's look at X -> Y"), e
  "Client disconnected. Stopping generation" ~120 s após o início.

## O que está acontecendo

1. O modelo põe TODO o pensamento em `message.reasoning_content` (campo à
   parte); `message.content` só recebe a resposta final. Se ele não terminar
   de pensar, `content` fica vazio.
2. Ele **entra em loop** quando o prompt tem ambiguidade que ele tenta
   resolver (ex.: "mantenho a palavra-chave Gherkin? o texto é PT ou EN?").
   Gasta o orçamento inteiro deliberando.
3. O **timeout do cliente HTTP** (padrão nosso era 120 s) derruba a geração
   no meio → `content` vazio mesmo sem erro do servidor.

## Procedure (as três defesas)

1. **Timeout generoso.** `httpx.Client(timeout=300)` — modelos locais de
   raciocínio levam minutos num documento longo. Timeout curto é a causa nº 1
   de `content` vazio com `finish_reason: stop`.
2. **Fallback para `reasoning_content`.** Ao ler a resposta OpenAI-compat: se
   `message["content"]` estiver vazio/branco, use `message["reasoning_content"]`
   como fonte de JSON (junto com a extração tolerante a raciocínio — ver
   [[saida-estruturada-llm-modelo-pequeno]]).
3. **Prompt determinístico, sem ambiguidade.** Não peça ao modelo para
   *decidir* regras. Dê a regra pronta e curta ("linha Given → pre_condicoes;
   copie o texto SEM a palavra-chave"). Ambiguidade vira loop de raciocínio.

## Anti-patterns

- Ler só `choices[0].message.content` e falhar "sem JSON" — o texto pode estar
  em `reasoning_content` e o `content` vazio por timeout.
- Prompt "explique como mapear" / listar variações de idioma: o modelo de
  raciocínio fixa nisso e não produz saída.
- Culpar a extração de JSON quando o problema é o cliente ter desconectado
  antes de o modelo terminar (veja o timestamp do "Client disconnected").

## UX correlata

- Import não deve submeter no `onChange` do arquivo: um modelo que leva
  minutos precisa de um botão "Enviar" explícito e feedback de progresso,
  senão o usuário acha que travou.

## Related material

- `backend/arbites/ai.py` — `_client` (timeout 300), `OpenAICompatible._raw_complete`
  (fallback `reasoning_content`), `_IMPORT_SYSTEM`.
- `frontend/src/components/TcRepository.tsx` — `AiImportModal` (botão Enviar).
- `backend/tests/test_ai_import_robustness.py`. Spec `ai-assist` (#6).
