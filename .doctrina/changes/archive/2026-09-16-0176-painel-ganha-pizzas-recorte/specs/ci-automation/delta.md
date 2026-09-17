# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

O painel respondia bem "está piorando?" e nada de "de que é feito" nem "qual
componente está pior". E a configuração ficava no meio do painel, tropeçando
todo dia em quem só queria ler.

```ops
append-requirement ubiquitous: The system shall exibir a divisão do período em gráfico de pizza — execuções por resultado e cenários por resultado — ao lado das séries, porque divisão e tendência são perguntas diferentes.
append-requirement unwanted: The system shall not deixar a cor de uma fatia carregar sozinha o significado; rótulo, valor e porcentagem acompanham cada fatia na legenda.
append-requirement ubiquitous: The system shall separar a observabilidade em Painel, Acessibilidade e Configuração, mantendo fora do painel diário o que se preenche uma vez.
append-requirement ubiquitous: The system shall exibir a saúde recortada por repositório e por rótulo declarado, do pior para o melhor.
append-criterion [verified] As três abas abrem em 390px e 1440px sem estouro horizontal; as pizzas desenham com uma e com várias fatias; o recorte por repositório e por rótulo aparece com o pior primeiro; e a aba de acessibilidade lista regra, gravidade, critério WCAG, elementos e página — verified by `backend/tests/test_recortes_observabilidade.py`, `backend/tests/test_export_observabilidade.py`.
set-header Last updated: 2026-09-16
bump-version minor
```
