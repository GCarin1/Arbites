# Spec Delta — capability: project-memory

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/project-memory/spec.md`

---

Dois fixes:

1. Falha ao gravar o evento de agente (disco, lock do índice) não perde
   mais a resposta que o LLM já gerou — `_log_agent_event` captura
   `OSError`/`sqlite3.Error` e vira warning; a resposta segue 200.
2. UI da timeline: desmarcar TODOS os tipos de filtro mostrava a timeline
   inteira (lista vazia virava `kinds=""` = "sem filtro" no backend) — agora
   mostra lista vazia, sem chamar a API.

- EARS: dois novos bullets Unwanted-behavior.
- Novo critério #7 — verified by `backend/tests/test_project_memory.py`
  (`test_agent_log_failure_does_not_lose_ai_response`).

Versão `0.1.0` → `0.1.1`.
