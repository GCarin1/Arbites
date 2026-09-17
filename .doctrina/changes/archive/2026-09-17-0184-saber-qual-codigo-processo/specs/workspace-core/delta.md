# Spec Delta — capability: workspace-core

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/workspace-core/spec.md`

---

"Atualizei e o erro continua" tem duas leituras — o conserto não funcionou,
ou o conserto não está rodando — e nada distinguia as duas.

```ops
append-requirement ubiquitous: The system shall informar, no arranque e na rota de saúde, qual código o processo está executando — ramo, commit, data do commit e se há alteração local não commitada —, para separar "o conserto não funcionou" de "o conserto não está rodando".
append-requirement unwanted: The system shall not inventar identidade de código quando não há checkout ao lado; nesse caso declara a ausência, porque um identificador plausível e errado é pior que nenhum.
append-criterion [verified] Em checkout git a identidade traz commit, ramo e o estado de alteração local; sem git, ou sem o binário do git, responde a ausência sem derrubar o processo; a rota de saúde devolve isso e continua aberta sem sessão — verified by `backend/tests/test_versao_em_execucao.py`.
set-header Last updated: 2026-09-17
bump-version minor
```
