# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

`python_path` é o executável do Python, mas o nome sugere `PYTHONPATH` e quem
preenche põe ali a pasta do projeto, a do virtualenv ou o `.env`. O valor
errado ia direto para o subprocess, e o run morria sem deixar rastro que a
tela mostrasse.

```ops
append-requirement event: When um alvo de automação é salvo com `python_path` que não resolve para um interpretador, the system shall recusar a gravação nomeando o alvo e o que o campo espera, em vez de aceitar um valor que só falha na hora de executar.
append-requirement ubiquitous: The system shall aceitar em `python_path` tanto o executável quanto a pasta de um virtualenv, resolvendo `Scripts/python.exe` ou `bin/python` dentro dela antes de recusar.
append-requirement event: When um run local é abortado antes de produzir resultado, the system shall registrar o motivo na própria execution — inclusive quando ela não tem nenhum CT vinculado — e exibi-lo na lista de runs, em vez de mostrar apenas "sem resultados".
append-criterion [verified] `python_path` vazio usa o Python do Arbites, pasta de virtualenv é resolvida, e arquivo de configuração, pasta sem interpretador e caminho inexistente são recusados ao salvar o alvo com código `bad_python_path`; um run abortado grava o motivo na execution e no índice mesmo sem nenhum CT — verified by `backend/tests/test_run_nao_executou.py`.
set-header Last updated: 2026-09-15
bump-version minor
```
