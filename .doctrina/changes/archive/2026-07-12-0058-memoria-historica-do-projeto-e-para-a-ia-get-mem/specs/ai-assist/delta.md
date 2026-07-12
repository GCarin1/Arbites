# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

`generate-testcases` e `review` passam a injetar, além da memória de longo
prazo do Perfil (`_with_memory`), um recap textual das decisões aceitas e
lições recentes do projeto (`project_memory.recent_recap`, ver capability
nova `project-memory`) — complementa a injeção de lições por similaridade
de palavra-chave já existente (critério #10), que só dispara quando há uma
palavra em comum entre a lição e a story/CT. O recap não depende de
similaridade textual: é sempre as N decisões aceitas e N lições mais
recentes, ou nenhum bloco quando o workspace não tem nenhuma das duas.

Adiciona:

- Um novo bullet Event-driven descrevendo a injeção do recap.
- Critério de aceitação #11 (verified by
  `backend/tests/test_project_memory.py`).
- Menção no Maturity → MVP.

Versão `0.9.0` → `0.10.0`.
