# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Requirements (EARS)

### Event-driven

- When o usuário solicita geração de CTs a partir de uma story, the system
  shall buscar defeitos com lição aprendida cujo título/causa/prevenção
  compartilhe palavra-chave (≥4 letras) com a story, injetar essas lições no
  prompt do provider (para não repetir a mesma causa), e expor na resposta
  `lessons_used` (quais lições foram consideradas) para o usuário ver o que
  influenciou a geração.

## Acceptance criteria

10. [verified] Gerar CTs a partir de uma story com lição aprendida relevante
   (palavra-chave em comum) injeta a lição no prompt enviado ao provider e
   devolve `lessons_used`; sem palavra em comum, `lessons_used` vem vazio e
   nada é injetado — verified by `backend/tests/test_lessons_learned.py`.
