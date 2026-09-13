# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

```ops
bump-version minor
append-requirement ubiquitous: The system shall carregar o `.env` do `local_path` do target e mesclá-lo no ambiente do subprocess do run — os valores do projeto ficam disponíveis ao Behave/WebDriver, sem sobrescrever `ARBITES_*` nem `PYTHONIOENCODING`.
append-requirement ubiquitous: The system shall derivar o catálogo de `.env` (`GET /env/catalog?target=`) das chaves, seções e comentários do próprio `.env`/`.env.example` do target, sem lista fixa embutida; sem target ou sem arquivo, o catálogo é vazio e o usuário adiciona chaves livres.
append-requirement event: When a aba de automação é reaberta com um run ativo, the system shall reconectar ao stream do run e restaurar o terminal a partir do replay do buffer do servidor.
append-requirement ubiquitous: The UI shall tornar o `EXEC-XXXX` do painel de run navegável para o board da execution e oferecer selecionar-todos/limpar no seletor de arquivos `.feature`.
append-criterion [unverified] O run injeta o `.env` do target no ambiente do subprocess (project vars disponíveis; `ARBITES_*`/`PYTHONIOENCODING` preservados) — verified by `backend/tests/test_local_runs.py`.
append-criterion [unverified] `GET /env/catalog` deriva chaves/seções do `.env`/`.env.example` do target e não expõe campos fixos de outro projeto — verified by `backend/tests/test_automation_targets_config.py`.
append-criterion [unverified] Terminal reconecta ao voltar à aba; `EXEC-` navega ao board; seletor de `.feature` tem selecionar-todos/limpar — verified by build + revisão visual.
```
