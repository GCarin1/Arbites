# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall exibir em cada card do Kanban, além do `testcase_id` e do
  título do CT, uma barra de progresso SEGMENTADA por passo: um segmento por
  step colorido pelo status (verde `passed`, vermelho `failed`, laranja
  `blocked`, trilho para `pending`), preenchendo até onde a execução chegou e
  misturando as cores na mesma linha.
- The system shall exibir a barra de progresso da execução como barra
  EMPILHADA por status: um segmento por status de resultado, largura
  proporcional à contagem, cada um na cor da sua coluna (não apenas `passed`).

## Acceptance criteria

5. [verified] O card reflete os status dos passos na barra segmentada e a
   barra da execução empilha todos os status (não só passed) — derivado de
   `results[].steps[]`/colunas, sem novo campo no backend — verified by
   `backend/tests/test_executions.py`.
