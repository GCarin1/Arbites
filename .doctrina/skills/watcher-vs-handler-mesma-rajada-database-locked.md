---
name: watcher-vs-handler-mesma-rajada-database-locked
description: Uma operação em lote no filesystem (mover/renomear uma pasta com vários arquivos) dispara uma rajada de eventos no filesystem watcher — cada um reindexando numa conexão SQLite própria — que colide com o loop de reindex do próprio handler HTTP (outra conexão), mesmo com busy_timeout configurado. Só aparece com carga real, nunca no TestClient (watch=False).
when: Ao adicionar/testar qualquer rota que faça uma operação de filesystem em LOTE (mover pasta, importar vários arquivos, excluir pasta) num app que também tem um watcher de filesystem reindexando em background.
---

# Skill — watcher-vs-handler-mesma-rajada-database-locked

## When to use this skill

- Vai adicionar uma rota que mexe em VÁRIOS arquivos de uma vez
  (mover/excluir/importar uma pasta inteira) num projeto que tem um watcher
  de filesystem (`watchdog`) reindexando em background.
- Um teste manual contra servidor real (não pytest) devolve 500 com
  `sqlite3.OperationalError: database is locked`, mas os testes automatizados
  passam limpo.

## Causa raiz

O app tem DUAS conexões SQLite: uma para os handlers HTTP
(`app.state.conn`) e outra, própria, para o watcher
(`watch_conn`, thread separada). Uma operação de UM arquivo só gera 1-2
eventos de filesystem — raramente colide. Uma operação em LOTE (renomear uma
pasta com N arquivos) gera uma RAJADA de N eventos que o watcher processa
(reindexando, numa conexão) quase ao mesmo tempo em que o handler HTTP
também reindexa os mesmos arquivos (na OUTRA conexão) — duas conexões
escrevendo no mesmo arquivo `.db` quase simultaneamente. `PRAGMA
busy_timeout` reduz a chance mas não cobre 100% dos casos.

**Por que os testes não pegam isso:** os testes de API sobem o app com
`watch=False` (sem thread de watcher) — então a corrida simplesmente não
existe no ambiente de teste. Só aparece rodando o servidor de verdade
(`python -m arbites serve`) e batendo via HTTP real.

## Procedure

1. **Reproduza com servidor real**, não só `TestClient`: suba
   `python -m arbites serve --port <N>` num workspace descartável e bata a
   rota em lote via `curl`/script, com N ≥ 3 arquivos afetados (1 arquivo
   raramente reproduz a corrida).
2. **Corrija na função compartilhada** (`reindex_file`), não na rota nova —
   o bug é do caminho de escrita compartilhado entre watcher e handlers,
   então uma correção pontual na rota só esconderia o sintoma ali.
3. **Retry com rollback**, não só retry cego: em
   `except sqlite3.OperationalError` (mensagem contém "locked"),
   `conn.rollback()` ANTES de tentar de novo — sem isso a transação parcial
   da tentativa anterior pode deixar a conexão num estado inconsistente.
4. Adicione um teste unitário do retry (monkeypatch para forçar
   `OperationalError` na 1ª chamada) — testável sem precisar do watcher real.

## Anti-patterns

- Confiar só em `PRAGMA busy_timeout` sem retry a nível de aplicação.
- "Consertar" só a rota nova (ex.: serializar as chamadas dentro dela) sem
  perceber que o watcher, numa OUTRA conexão, ainda pode colidir.
- Validar só com `TestClient` (`watch=False`) e declarar "funciona" sem
  testar contra um servidor real com o watcher ligado.

## Related material

- `backend/arbites/indexer.py` — `reindex_file` (retry+rollback),
  `_reindex_file_once`.
- `backend/arbites/watcher.py` — conexão própria do watcher.
- `backend/arbites/api.py` — `app.state.conn` vs `watch_conn` (linhas ~362-375).
- `backend/tests/test_indexing.py` —
  `test_reindex_file_retries_transient_database_locked`.
