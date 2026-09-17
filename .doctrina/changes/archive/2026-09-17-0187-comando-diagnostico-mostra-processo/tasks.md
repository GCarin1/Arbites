# Tasks — Change 0187-comando-diagnostico-mostra-processo

- [x] `envfile`: `localizar()` subindo até a raiz do projeto.
- [x] `envfile`: ler com `utf-8-sig`, `descartadas()` e `pista_do_valor()`.
- [x] `backend/arbites/diagnostico.py` com as cinco seções.
- [x] Subcomando `diagnostico` na CLI; o arranque imprime qual `.env` leu.
- [x] README: a seção do diagnóstico e onde o `.env` precisa estar.
- [x] `tls`: pista do valor na mensagem de tela e ponteiro para o comando.
- [x] `backend/tests/test_diagnostico.py`.
- [x] `conftest`: restaurar `os.environ` entre testes — o vazamento
      que fazia um teste de outro arquivo falhar só na suíte.
- [x] Executar o comando contra um `.env` quebrado de verdade.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-17-0187-comando-diagnostico-mostra-processo/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
