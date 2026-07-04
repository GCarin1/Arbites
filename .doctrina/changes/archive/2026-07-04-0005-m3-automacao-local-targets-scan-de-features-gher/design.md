# Design — Change 0005-m3-automacao-local-targets-scan-de-features-gher

## Approach

Três módulos com fronteiras limpas: `gherkin_scan.py` (pacote oficial
`gherkin` → tabela `scenarios` + warnings, chamado pelo reindex e pelo
scan manual), `behave_json.py` (Cucumber JSON → modelo neutro de
resultados; adapter único que o M4 reutiliza na coleta por artifact, com
fixtures versionadas como contrato) e `runner.py` (ciclo do run local).

O runner mantém um `RunManager` no app state: fila FIFO `asyncio` por
target (lock implícito — um worker por target consome a fila), timeout via
`asyncio.wait_for`, stdout acumulado em buffer por run e retransmitido por
SSE (quem conecta tarde recebe o buffer e segue ao vivo). O comando é
`[python_path|python, "-m", "behave", "-f", "json", "-o", tmp/result.json,
"-f", "plain", "--tags=...", local_path]` com `ARBITES_EVIDENCE_DIR`
injetada; ao terminar, o JSON é parseado, evidências capturadas pelos
hooks são movidas para a execution e hasheadas, e os resultados entram no
mesmíssimo `execution.json` do fluxo manual.

Os testes usam **behave de verdade** (dependência de dev) contra um
mini-repo fixture com features em `# language: pt` e um `environment.py`
que honra o contrato `ARBITES_EVIDENCE_DIR` — o SC5 é exercitado de ponta
a ponta sem Selenium.

## Alternatives considered

- Mockar o subprocess do Behave — rejeitado: o parse do JSON e o contrato
  de evidências são exatamente o que precisa de prova real; behave é puro
  Python e leve.
- Lock explícito por target — rejeitado: fila com worker único por target
  dá FIFO e exclusão mútua com menos estado.

## Trade-offs and risks

- SSE com buffer em memória: logs muito grandes ficam na RAM até o fim do
  run — aceitável no volume alvo; rotação pode vir depois.
- `asyncio.Queue` amarra o runner ao event loop do uvicorn — testes usam
  o TestClient (mesmo loop), produção é single-process (ADR 0004).

## Decisions to record as ADRs

Nenhuma nova — executa ADRs 0003 (tag @CT) e 0004 (subprocess).
