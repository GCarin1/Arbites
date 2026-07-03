# Design — Change 0001-m0-fundacao-workspace-parsers-reindex-api-de-req

## Approach

Monólito local em dois diretórios: `backend/` (pacote `arbites`, FastAPI +
Pydantic v2, SQLite via stdlib) e `frontend/` (React 18 + Vite + TS). O
backend resolve o workspace por variável `ARBITES_WORKSPACE` (default:
`./workspace`) e garante a estrutura na subida (cria pastas, `arbites.yaml`
default e `counters.json` se ausentes — primeira execução sem fricção). O
indexer é uma função pura `reindex_full(workspace, db)` + `reindex_file`
para o incremental; o watcher (watchdog) é uma casca fina que chama
`reindex_file`, então os testes exercitam a função diretamente e ficam
determinísticos. A UI consome `/api/v1` e é servida de `frontend/dist`
pelo próprio FastAPI quando o build existe.

## Alternatives considered

- Pacote instalável com pyproject + entry points — adiado: um
  `requirements.txt` + `uvicorn arbites.api:app` cumpre o M0 com menos
  cerimônia; empacotamento vem quando houver CLI (`arbites reindex` já
  existe como `python -m arbites.reindex`).
- Testes de watcher com eventos reais do SO — rejeitado: timing flaky no
  Windows; o handler é testado por chamada direta.

## Trade-offs and risks

- `tsc` no build do frontend mantém o gate honesto mas torna o build
  sensível a tipos — aceito, código é nosso.
- Teste de performance (2.000 CTs < 5 s) depende da máquina; roda com
  arquivos mínimos e margem larga.

## Decisions to record as ADRs

Nenhuma nova — o M0 implementa ADRs 0001, 0002 e 0009 já aceitos.
