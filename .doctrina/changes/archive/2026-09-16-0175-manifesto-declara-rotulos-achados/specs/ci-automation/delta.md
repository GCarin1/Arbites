# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

Duas lacunas que só aparecem num projeto de verdade: o repositório onde o
workflow mora não é o que está sob teste, e `violacoes_axe: 14` diz que
piorou sem dizer o quê.

```ops
append-requirement ubiquitous: The system shall aceitar no manifesto do artifact um bloco `labels` de chave livre declarando o que aquela execução validou — componente, ambiente, camada — e continuar aceitando manifestos da versão anterior.
append-requirement ubiquitous: The system shall registrar achados estruturados por execução com regra, gravidade, critério da WCAG, quantidade de elementos e página, lendo nativamente o JSON do axe-core publicado como anexo, sem exigir que o pipeline o reescreva.
append-requirement ubiquitous: The system shall responder a saúde recortada por repositório de origem e por rótulo declarado, além da divisão do período por resultado de execução e de cenário.
append-requirement unwanted: The system shall not oferecer como recorte um rótulo com um único valor ou com valores demais; um valor não divide nada e um por execução é identificador, não dimensão.
append-criterion [verified] O critério da WCAG sai da tag do axe, o número é de elementos e não de regras, JSON quebrado não derruba a ingestão, achado declarado e lido do axe têm a mesma forma e somam; rótulo de valor único e de cardinalidade alta ficam fora do recorte; e cada repositório responde a própria taxa, pior primeiro — verified by `backend/tests/test_manifesto_v2.py`, `backend/tests/test_recortes_observabilidade.py`.
set-header Last updated: 2026-09-16
bump-version minor
```
