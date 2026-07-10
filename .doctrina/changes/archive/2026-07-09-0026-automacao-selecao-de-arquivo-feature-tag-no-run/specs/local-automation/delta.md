# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

## Context

Doc de ajustes §1.5.1: run local com seleção de arquivo `.feature` + tag
(comando `behave <arquivo> --tags=<tag>` montado na UI com dropdowns/
autocomplete), acesso aos artefatos pós-execução (./logs, ./screenshots,
./analise) e editor visual do `.env` do projeto com catálogo de variáveis
descritas.

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall expor `GET /targets/{name}/features` (arquivos .feature e
  tags do target, a partir do scan) para os dropdowns do run.
- The system shall aceitar `feature` opcional em `POST /runs/local`, passando
  o arquivo como argumento posicional do behave (`behave <arquivo> --tags=`).
- The system shall listar e servir os artefatos pós-execução do target
  (`./logs`, `./screenshots`, `./analise`) via
  `GET /targets/{name}/artifacts[/file]`, com guarda de path traversal.
- The system shall expor edição visual do `.env` do target
  (`GET/PUT /targets/{name}/env` + `GET /env/catalog` com nome/descrição por
  variável), preservando comentários e linhas desconhecidas no PUT.

## Acceptance criteria (ADDED)

5. [verified] Features e tags do target expostos p/ seleção; run aceita
   feature específico — verified by `backend/tests/test_automation_flow.py`.
6. [verified] Artefatos listados e baixáveis com traversal bloqueado —
   verified by `backend/tests/test_automation_flow.py`.
7. [verified] `.env` editável por chave com comentários e linhas
   desconhecidas preservados; catálogo com descrições — verified by
   `backend/tests/test_automation_flow.py`.
