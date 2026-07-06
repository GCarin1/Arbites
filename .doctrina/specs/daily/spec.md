# Spec — daily

**Capability:** daily
**Status:** active
**Implementation:** verified — M11 (backend/arbites/daily.py, backend/arbites/api.py, backend/arbites/ai.py; frontend Daily.tsx). IA opcional (reusa provider do M5); snapshots em `metrics/`, dailies em `dailies/`
**Realizes:** SC12
**Last updated:** 2026-07-06
**Version:** 0.2.0

## Purpose

Uma página Daily que ajuda o QA a chegar na daily standup com o texto pronto:
resumo executivo do dia anterior, impedimentos e andamento. A IA (opcional,
M5) faz a digestão de quatro fontes que a plataforma já tem — os **todos**
(feitos/pendentes/bloqueados), a **atividade do QA** do dia (execuções
rodadas, defeitos abertos), o **diff de métricas** (via snapshot diário) e o
**registro de defeitos** — e propõe o texto + os **action items**. Nada é
gravado sem aceite; os action items viram todos (com confirmação). Sem
provider de IA, a página segue funcional (você escreve a daily à mão sobre o
mesmo contexto).

## Requirements (EARS)

### Ubiquitous

- The system shall gravar um snapshot diário das métricas em
  `metrics/AAAA-MM-DD.json` para permitir comparação antes/depois entre dias.
- The system shall montar o contexto de um dia a partir dos todos, da
  atividade do QA (execuções e defeitos daquele dia), do diff de métricas
  (snapshot do dia vs. do dia anterior) e dos defeitos abertos.
- The system shall persistir a daily de um dia como `dailies/AAAA-MM-DD.md`
  (frontmatter com `date` e `action_items`; corpo com o texto), editável.
- The system shall expor `GET /dailies` (datas com daily), `GET/PUT
  /daily/{date}`, `GET /daily/{date}/context` e `POST /metrics/snapshot`.

### Event-driven

- When o usuário solicita gerar a daily de um dia e há provider de IA
  configurado, the system shall devolver um preview com resumo executivo,
  impedimentos, andamento e action items — sem gravar nada.
- When o usuário aceita um action item, the system shall criar um todo
  correspondente (loop reunião/daily → trabalho rastreável).

### State-driven

- While nenhum provider de IA está configurado, the system shall entregar o
  contexto do dia para escrita manual da daily, sem quebrar a página.

### Unwanted-behavior (must-not)

- The system shall not gravar a daily nem os todos derivados sem ação
  explícita do usuário (toda saída de IA é preview).
- The system shall not tornar a página Daily dependente de IA (funciona
  para consulta/escrita manual sem provider).

### Optional

- Where há resumos de reunião do dia (M12), the system may incluí-los no
  contexto da digestão da daily.

## Acceptance criteria

1. [verified] Snapshot de métricas é gravado por dia e o contexto expõe o
   diff do dia vs. dia anterior — verified by `backend/tests/test_daily.py`.
2. [verified] O contexto do dia agrega todos (incl. bloqueados),
   atividade (execuções/defeitos do dia) e defeitos abertos — verified by
   `backend/tests/test_daily.py`.
3. [verified] Gerar a daily com um provider (mock) devolve resumo,
   impedimentos, andamento e action items em preview, sem gravar — verified
   by `backend/tests/test_daily.py`.
4. [verified] Salvar a daily persiste `dailies/AAAA-MM-DD.md` e ela aparece
   em `GET /dailies`; aceitar um action item cria um todo — verified by
   `backend/tests/test_daily.py`.

## Maturity

**MVP (committed):**

- Snapshot diário, contexto do dia, geração por IA (preview), salvar/listar
  daily por data, action items → todos.

**Future (aspirational, not committed):**

- Calendário em grade mensal; resumo semanal; ingestão de reuniões (M12).

## Out of scope for this spec

- Aba de reuniões e sua digestão (é M12).
- Automação de agendamento/lembrete da daily.
