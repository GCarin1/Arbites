# Design — Change 0003-m1-5-dashboard-e-rastreabilidade-7-metricas-tend

## Approach

Métricas são queries puras sobre o índice SQLite (ADR 0001) num módulo
`metrics.py` sem estado — cada função recebe a conexão e os filtros e
devolve o número com numerador/denominador explícitos (as fórmulas são
defensáveis em reunião; a API nunca esconde o denominador). Para
retrabalho, flaky e tendência é preciso o histórico de transições, não só
o status atual: o indexer ganha a tabela `result_events`, populada do
`history[]` do execution.json no mesmo scan (o banco é descartável, então
não há migração — reindex reconstrói). A matriz agrega por story o último
resultado final de cada CT (pior status entre os últimos: failed >
blocked > retest > passed), com contagens de evidências e defeitos, e
cada nível é clicável até o download do arquivo de evidência
(`GET .../evidences/{index}/file`). Export MD é renderização da mesma
estrutura; PDF via `fpdf2` (puro Python, leve).

## Alternatives considered

- Guardar métricas materializadas — rejeitado: o índice é descartável e as
  queries são triviais no volume alvo (milhares de resultados).
- PDF via headless browser — rejeitado: dependência pesada; fpdf2 gera a
  tabela diretamente.
- Trend por `executed_at` do resultado (status final) — rejeitado: perde
  transições intermediárias; `result_events` registra cada mudança.

## Trade-offs and risks

- `result_events` duplica parte do history no índice — aceito, é índice
  (descartável e reconstruível).
- Flaky definido como "houve transição pass↔fail entre execuções
  consecutivas na janela N" — definição explícita na resposta da API.

## Decisions to record as ADRs

Nenhuma nova — consome ADRs 0001 e 0005.
