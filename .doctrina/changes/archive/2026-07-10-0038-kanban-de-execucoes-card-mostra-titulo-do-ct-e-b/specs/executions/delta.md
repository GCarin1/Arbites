# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall exibir em cada card do Kanban, além do `testcase_id`: o
  título do caso de teste e, quando o resultado tiver passos estruturados,
  uma barra de progresso com o percentual de passos `passed` em relação ao
  total.
- The system shall abrir a edição de um resultado (passos, evidências,
  comentário, defeitos) num modal centralizado com botão de fechar (X),
  não mais como painel inline abaixo do Kanban.

## Acceptance criteria

5. [verified] Marcar um passo como `passed` reflete no percentual exibido no
   card correspondente (derivado de `results[].steps[]`, sem novo campo no
   backend) — verified by `backend/tests/test_executions.py`.
