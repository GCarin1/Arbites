# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer uma area de observabilidade separada do painel de indicadores, com o tempo como eixo primario, comparacao com o periodo anterior e descida do agregado ate a execucao, o job e o anexo.
append-requirement ubiquitous: The system shall declarar em cada bloco da area de observabilidade a pergunta que ele responde, e nao exibir bloco que nao responda a uma pergunta acionavel.
append-criterion [unverified] De um ponto da serie temporal chega-se a execucao, ao job e ao anexo sem sair da aba; periodo sem dado mostra estado vazio util; em 390 px a pagina nao rola de lado — verified by `backend/tests/test_observability.py`.
bump-version minor
```
