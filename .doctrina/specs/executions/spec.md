# Spec — executions

**Capability:** executions
**Status:** active
**Implementation:** verified — M1 (backend/arbites/executions.py, backend/arbites/api.py, frontend/src/components/Executions.tsx)
**Realizes:** SC2
**Last updated:** 2026-07-10
**Version:** 0.4.0

## Purpose

Gerencia ciclos de execução de teste (executions) como `execution.json` em
`executions/<ano>/EXEC-XXXX/`, com resultados por CT, steps marcáveis,
evidências hasheadas e histórico de eventos. O Kanban da UI opera sobre
resultados dentro de uma execution — nunca sobre o documento do CT.

## Requirements (EARS)

### Ubiquitous

- The system shall persistir cada execution como `execution.json`
  (`schema_version`, `id`, `name`, `owner`, `sprint`, `environment`,
  `origin`, `created_at`, `closed_at`, `status`, `ci`, `results[]`,
  `history[]`) conforme o contrato do intake (§5.5).
- The system shall manter três máquinas de estado independentes:
  execution (`draft → in_progress → closed`), resultado
  (`pending → in_progress → passed|failed|blocked|retest` + coluna
  `closed`) e documento do CT (fora deste spec).
- The system shall aceitar `origin` em `manual | local_run |
  github_actions`.
- The system shall tratar `sprint` e `environment` como texto livre.
- The system shall armazenar evidências em
  `EXEC-XXXX/evidences/CT-XXXX/`, registrando caminho relativo, SHA-256,
  MIME e timestamp.
- The system shall expor a API do M1: `GET/POST /executions`,
  `GET/PATCH /executions/{id}`, `POST .../results/{ct}/status`,
  `POST .../results/{ct}/steps/{n}`,
  `POST/DELETE .../results/{ct}/evidences`, `POST .../close`.
- The system shall apresentar o Kanban com colunas
  `Pending | In Progress | Blocked | Failed | Retest | Passed`.
- The system shall exibir em cada card do Kanban, além do `testcase_id` e do
  título do CT, uma barra de progresso SEGMENTADA por passo: um segmento por
  step colorido pelo status (verde `passed`, vermelho `failed`, laranja
  `blocked`, trilho para `pending`), preenchendo até onde a execução chegou e
  misturando as cores na mesma linha.
- The system shall exibir a barra de progresso da execução como barra
  EMPILHADA por status: um segmento por status de resultado, largura
  proporcional à contagem, cada um na cor da sua coluna (não apenas `passed`).
- The system shall abrir a edição de um resultado (passos, evidências,
  comentário, defeitos) num modal centralizado com botão de fechar (X),
  não mais como painel inline abaixo do Kanban.

### Event-driven

- When um card é arrastado no Kanban, the system shall atualizar o
  `execution.json`, gravar evento no `history[]` e reindexar.
- When uma evidência é enviada (multipart), the system shall gravá-la no
  disco sob a execution, calcular SHA-256 e registrar no resultado.
- When um resultado muda de status, the system shall registrar evento
  `{at, who, event: "result", testcase_id, to}` no `history[]`.
- When a execution é fechada, the system shall preencher `closed_at` e
  mudar `status` para `closed`.

### State-driven

- While uma execution está `closed`, the system shall rejeitar alterações
  de resultados nela.

### Unwanted-behavior (must-not)

- The system shall not misturar status do documento CT com status de
  resultado; o mesmo CT pode estar `passed` na EXEC-0001 e `failed` na
  EXEC-0002 sem contradição.
- The system shall not exigir cadastro prévio de sprint ou ambiente.

### Optional

- Where um step individual é marcado, the system may persistir o status
  por step em `results[].steps[]`.

## Acceptance criteria

1. [verified] Regressão manual de ~20 CTs com evidências e defeito
   vinculado completa sem sair da plataforma — verified by
   `backend/tests/test_executions_e2e.py`.
2. [verified] Drag no Kanban persiste no `execution.json` e gera evento
   de history — verified by `backend/tests/test_executions.py`.
3. [verified] Upload de evidência grava arquivo + SHA-256 corretos —
   verified by `backend/tests/test_executions.py`.
4. [verified] Mesmo CT com resultados distintos em duas executions não
   gera conflito — verified by `backend/tests/test_executions.py`.

5. [verified] O card reflete os status dos passos na barra segmentada e a
   barra da execução empilha todos os status (não só passed) — derivado de
   `results[].steps[]`/colunas, sem novo campo no backend — verified by
   `backend/tests/test_executions.py`.

## Maturity

**MVP (committed):**

- Executions manuais, Kanban, steps marcáveis, evidências com hash,
  history, fechamento.

**Future (aspirational, not committed):**

- Re-execução em lote ("retestar todos os failed"); templates de
  execution.

## Out of scope for this spec

- Runs automatizados que criam executions (ver `local-automation`,
  `ci-automation`).
- Defeitos (ver `defects`).
