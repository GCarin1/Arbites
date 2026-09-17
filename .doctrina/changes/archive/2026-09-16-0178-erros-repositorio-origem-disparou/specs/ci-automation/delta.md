# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

Um repositório de teste serve vários produtos. Sem saber quem mandou rodar,
"qual produto está quebrando" não tem resposta.

```ops
append-requirement ubiquitous: The system shall registrar por execução o repositório de origem que disparou a suíte, com ambiente e referência, declarado no bloco `trigger` do manifesto ou num rótulo de nome conhecido.
append-requirement ubiquitous: The system shall responder a saúde e o volume de falhas recortados por repositório de origem, ao lado do recorte por repositório de teste — um repositório de teste serve vários produtos e só o primeiro recorte responde qual produto está quebrando.
append-requirement unwanted: The system shall not inferir o repositório de origem de uma execução que não o declara; sem declaração a execução fica fora do recorte, porque adivinhar a topologia erraria na primeira exceção.
append-criterion [verified] O bloco `trigger` é lido com nomes alternativos de campo e ganha do rótulo; a ausência não inventa origem; um repositório de teste servindo dois produtos responde uma taxa por produto; e o gráfico de erros conta volume de falha, não taxa — verified by `backend/tests/test_origem_do_disparo.py`.
set-header Last updated: 2026-09-16
bump-version minor
```
