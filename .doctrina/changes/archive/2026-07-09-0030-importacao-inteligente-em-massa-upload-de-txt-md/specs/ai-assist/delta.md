# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

## Context

Doc de ajustes §1.1 (Importação Inteligente): upload de `.txt`/`.md`/`.xml`
com casos de teste em formato livre; a IA identifica cada caso, sugere uma
pasta pelo contexto e converte para BDD (Given/When/Then) em preview
aceitável item a item. Prompt curto de propósito (modelos ≤ 9B).

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall expor `POST /import/ai` (upload .txt/.md/.xml) que usa a
  IA para identificar os casos do texto livre, sugerir uma pasta e convertê-
  los para BDD — sempre preview; o aceite é o `POST /testcases` normal.
- The system shall manter o prompt de importação enxuto (sem exemplos
  longos; texto truncado) para operar bem em modelos de até 9B.

## Acceptance criteria (ADDED)

4. [verified] Arquivo livre vira preview BDD (pasta sugerida + Given/When/
   Then), nada gravado sem aceite; extensão inválida e arquivo vazio → 422 —
   verified by `backend/tests/test_ai_import.py`.
