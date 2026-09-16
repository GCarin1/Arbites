# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

O painel só existia na tela. Levá-lo para uma reunião, uma ata ou uma
planilha exigia print — e print de série temporal não se cruza com nada.

```ops
append-requirement ubiquitous: The system shall exportar o painel de observabilidade do período escolhido em PDF com os gráficos desenhados, em CSV com uma linha por medida, e em Markdown legível sem leitor especial.
append-requirement unwanted: The system shall not depender de captura de tela para exportar os gráficos; a série é desenhada no próprio arquivo, porque exportar não pode exigir um navegador aberto.
append-requirement unwanted: The system shall not afirmar melhora ou piora de um sinal sem direção declarada na exportação, pela mesma razão que não afirma na tela — a semântica é de quem instala.
append-criterion [verified] Os três formatos saem como anexo nomeado pelo período; o CSV traz uma linha por medida com a execução de origem; o Markdown não afirma piora de sinal sem direção declarada; o PDF é PDF com painel vazio, com série constante e com várias mudanças — verified by `backend/tests/test_export_observabilidade.py`.
set-header Last updated: 2026-09-16
bump-version minor
```
