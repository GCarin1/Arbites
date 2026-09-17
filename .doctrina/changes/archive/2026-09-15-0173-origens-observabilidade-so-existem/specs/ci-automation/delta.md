# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

As origens da observabilidade só existiam no `arbites.yaml`. Numa instalação
nova, "Buscar execuções" respondia "nenhuma fonte" e não havia onde declarar
uma sem abrir o arquivo à mão.

```ops
append-requirement ubiquitous: The system shall permitir declarar e remover as origens da observabilidade pela própria tela, gravando-as no `arbites.yaml`, sem exigir que o operador edite o arquivo à mão.
append-requirement state: While nenhuma origem está declarada, the system shall dizer isso na tela de observabilidade junto do campo que a declara, em vez de apenas informar que nenhuma execução chegou.
append-requirement unwanted: The system shall not gravar `workflow` ou `artifact` vazios como valor; ausentes significam "todos", e a chave vazia faria a ingestão procurar um nome que nunca existe.
append-criterion [verified] Instalação nova responde lista vazia; declarar grava no `arbites.yaml` e é exatamente o que a ingestão enxerga; workflow e artifact em branco não viram chave; origem sem repositório é descartada; escrever exige `admin` e ler não — verified by `backend/tests/test_origens_observabilidade.py`.
set-header Last updated: 2026-09-15
bump-version minor
```
