# Spec — reporting

**Capability:** reporting
**Status:** active
**Implementation:** verified — M1.5 + M7 (filtro squad) + M8 (metas/thresholds) + M9 (painel de defeitos); backend/arbites/metrics.py, backend/arbites/api.py, backend/arbites/export_pdf.py, frontend/src/components/Dashboard.tsx
**Realizes:** SC3
**Last updated:** 2026-07-10
**Version:** 0.9.0

## Purpose

Dashboard e matriz de rastreabilidade para reporte à gestão — a dor
declarada número um. Métricas escolhidas por serem defensáveis em reunião,
com fórmula explícita, calculadas por queries no índice SQLite. Inclui
export PDF e Markdown (para colar no Confluence).

## Requirements (EARS)

### Ubiquitous

- The system shall calcular as 7 métricas com as fórmulas do intake (§11):
  cobertura de requisito (stories `active` com ≥1 CT `ready` ÷ stories
  `active`), cobertura de execução, pass rate (`passed` ÷ `passed`+`failed`),
  taxa de bloqueio, retrabalho (passaram por `retest` ÷ total),
  instabilidade/flaky (alternância pass/fail em janela N) e tendência
  diária (7/15/30 dias).
- The system shall calcular a tendência diária contando cada par
  (execução, testcase) **uma vez por dia**, pelo status da última
  transição registrada naquele dia — nunca somando transições
  intermediárias.
- The system shall expor `GET /metrics/summary`, `/metrics/trend`,
  `/metrics/coverage`, `/metrics/traceability`, `/metrics/flaky` com os
  filtros do contrato (sprint, days, epic, window).
- The system shall renderizar a matriz de rastreabilidade
  Epic → Story | CTs | Último resultado | Execution | Evidências |
  Defeitos, com cada célula clicável até o arquivo de evidência
  (drill-down completo).
- The system shall marcar stories sem CT como "sem cobertura" na matriz.
- The system shall exportar a matriz em PDF e em Markdown.
- The system shall anotar cada métrica do summary com um `status`
  (ok/warn/bad/none) contra metas opcionais configuradas em `arbites.yaml`
  (`metric_thresholds`), respeitando a direção da métrica (maior-melhor ou
  menor-melhor).
- The system shall expor `GET /metrics/defects` com um resumo dos defeitos
  abertos: contagem total, por severidade, por squad e por faixa de aging
  (dias em aberto), além da lista, filtrável por squad.
- The system shall expor `GET /metrics/automation` que agrega as execuções de
  automação (`origin != manual`) do período, agrupadas por REPOSITÓRIO
  extraído do NOME da execução via regex configurável
  (`ci_monitoring.name_pattern` no `arbites.yaml`, com grupos nomeados `repo`
  obrigatório e `env` opcional; default genérico, sem referência a
  empresa/projeto), com o desfecho de cada run (passed/failed/…) derivado dos
  seus `results[]`.
- The system shall ordenar os repositórios do relatório de automação
  pior-primeiro (mais falhas, depois maior taxa de falha), reportar
  passed/failed/pass_rate por repo e por ambiente, e contar em `unparsed` os
  runs cujo nome não casa o padrão (sinal de padrão a ajustar).
- The system shall enriquecer `GET /metrics/automation` com: os CTs que mais
  falham nos runs de automação (`top_failing_testcases`, pior-primeiro); por
  repositório, o histórico recente de desfechos (`recent`, para sparkline), o
  MTTR em horas (tempo médio até voltar ao verde) e `broken_since` quando o
  repo segue vermelho, e a contagem de CTs flaky (`flaky`); e a lista global
  de CTs flaky em automação (`flaky_testcases`).
- The system shall aceitar o filtro opcional `env` em `GET /metrics/automation`
  (ambiente extraído do nome), mantendo `envs` com todos os ambientes
  disponíveis para o seletor mesmo quando filtrado.
- The system shall expor `GET /metrics/activity` que agrega a atividade de QA
  por dia nos últimos ~12 meses (janela alinhada à segunda-feira, para a grade
  Seg→Dom × semanas), somando por dia: casos executados (transições de
  resultado), bugs abertos, CTs e requisitos criados e runs de automação;
  devolvendo apenas os dias com atividade (o cliente preenche os zeros) mais os
  totais do período.
- The system shall aceitar o filtro opcional `year` em `GET /metrics/activity`
  (janela do ano civil, alinhada à segunda-feira), e devolver `years` — os
  anos que têm atividade — para o seletor de ano do heatmap.

### Event-driven

- When o usuário aplica filtro de epic ou sprint, the system shall
  recalcular matriz e métricas sobre o subconjunto filtrado.
- When o usuário passa o mouse sobre uma célula do heatmap de atividade, the
  system shall exibir um tooltip com o número de mudanças (atividade) daquele
  dia e o detalhamento por tipo.

### State-driven

- While não há dados de execução no período, the system shall exibir
  métricas zeradas com denominadores explícitos (nunca esconder a fórmula).
- While nenhuma meta está configurada para uma métrica, the system shall
  reportar `status: none` e não colorir o card (número e fórmula seguem
  visíveis).

### Unwanted-behavior (must-not)

- The system shall not contabilizar resultados não-finais (`pending`,
  `in_progress`) no pass rate.
- The system shall not inflar a tendência contabilizando transições
  intermediárias de status: reordenar/re-arrastar um mesmo CT entre
  colunas no mesmo dia não pode aumentar a contagem daquele dia.
- The system shall not usar cor como único indicador de status (sempre
  ponto colorido + texto).
- The system shall not derrubar `GET /metrics/automation` quando a regex
  configurada é inválida; deve cair no padrão default e reportar
  `pattern_error`.
- The system shall not referenciar nenhuma empresa/organização/projeto
  específico no padrão default nem na spec (o padrão é genérico e
  sobrescrevível).

### Optional

- Where a janela de flaky N é configurada, the system may recalcular a
  instabilidade sobre as últimas N execuções.

## Acceptance criteria

1. [verified] Reporte de sprint gerado em < 1 minuto com drill-down até
   evidência — verified by `backend/tests/test_reporting_e2e.py`.
2. [verified] Cada métrica bate com a fórmula sobre um dataset fixture
   conhecido — verified by `backend/tests/test_metrics.py`.
3. [verified] Export Markdown da matriz é colável no Confluence sem
   perda de estrutura — verified by `backend/tests/test_export.py`.
4. [verified] Export PDF gerado com a matriz navegada — verified by
   `backend/tests/test_export.py`.
5. [verified] Um único CT arrastado por vários status no mesmo dia conta
   como 1 no status final do dia na tendência, não como vários — verified
   by `backend/tests/test_metrics.py`.
6. [verified] Cada métrica recebe status ok/warn/bad conforme a meta e a
   direção configuradas, e `none` quando não há meta — verified by
   `backend/tests/test_metrics.py`.
7. [verified] O report de defeitos agrega os defeitos abertos por
   severidade, squad e faixa de aging, e filtra por squad — verified by
   `backend/tests/test_defects.py`.

8. [verified] `GET /metrics/automation` agrupa runs de automação por repo
   (pior-primeiro), deriva passed/failed por run dos resultados, ignora
   execuções manuais, conta `unparsed` e respeita um `name_pattern`
   customizado; regex inválida não derruba a rota (reporta `pattern_error`)
   — verified by `backend/tests/test_automation_report.py`.

9. [verified] `GET /metrics/automation` expõe ranking de CTs que mais falham,
   sparkline/MTTR/`broken_since`/flaky por repo, lista global de flaky, e o
   filtro `env` (com `envs` completo) — verified by
   `backend/tests/test_automation_report.py`.

10. [verified] `GET /metrics/activity` agrega os sinais datados por dia
    (casos executados/bugs/CTs/requisitos/runs), com a janela começando numa
    segunda-feira e cobrindo ~53 semanas, e devolve os totais — verified by
    `backend/tests/test_activity_heatmap.py`.

11. [verified] `GET /metrics/activity?year=` janela o ano civil (alinhado à
    segunda) e a resposta lista os anos com atividade; sem filtro segue os
    últimos ~12 meses — verified by `backend/tests/test_activity_heatmap.py`.

## Maturity

**MVP (committed):**

- 7 métricas, tendência, matriz navegável, export PDF/MD, metas/thresholds
  por métrica (semáforo), painel de defeitos abertos (aging/severidade/squad),
  monitoramento de automação por repositório (pior-primeiro, padrão de nome
  configurável, sparkline/MTTR/flaky por repo, CTs que mais falham, filtro de
  ambiente), heatmap de atividade de QA no perfil (estilo GitHub).

**Future (aspirational, not committed):**

- Comparação entre sprints.

## Out of scope for this spec

- Coleta dos dados (ver `executions`, `indexing`).
