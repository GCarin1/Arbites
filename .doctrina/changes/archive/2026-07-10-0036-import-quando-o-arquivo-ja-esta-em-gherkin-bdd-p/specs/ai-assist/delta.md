# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Requirements (EARS)

### Event-driven

- When o arquivo enviado para importação já está em Gherkin/BDD (contém
  Scenario + passos Given/When/Then), the system shall separá-lo por um parser
  determinístico e preservar o texto VERBATIM (Feature, título e cada passo,
  inclusive múltiplos And), sem IA e sem exigir provider configurado — não
  deve parafrasear, trocar a Feature pelo título, adicionar pontuação nem
  fundir passos.

## Acceptance criteria

8. [verified] Importar um .txt já em Gherkin devolve o corpo idêntico ao
   enviado (Feature preservada, "que" e ambos os And intactos), com a pasta =
   slug da Feature, sem tocar no provider de IA — verified by
   `backend/tests/test_ai_import.py`.
