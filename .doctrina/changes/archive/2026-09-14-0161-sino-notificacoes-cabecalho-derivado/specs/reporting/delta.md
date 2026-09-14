# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

```ops
append-requirement ubiquitous: The system shall apresentar um sino de notificacoes no cabecalho com a quantidade de itens nao lidos, derivando a lista do estado vivo das fontes existentes em vez de manter uma caixa de entrada gravada, para que um motivo resolvido saia da lista sozinho.
append-requirement ubiquitous: The system shall guardar por usuario apenas o que foi lido e ate onde foi limpo, com identificador estavel por notificacao, para que a marca de leitura sobreviva ao recalculo da lista.
append-requirement ubiquitous: The system shall levar da notificacao ao artefato de origem, e apresentar o nome do arquivo ou do item em destaque separado do texto da mensagem.
append-requirement state: While o interruptor de log esta desligado ou o usuario nao e administrador, the system shall not incluir o log de atividade no sino.
append-criterion [unverified] Problema resolvido sai do sino mesmo sem leitura; o sino e a tela de problemas leem a mesma lista; lido e por pessoa e sobrevive ao recalculo; limpar e marca d'agua; log de atividade so alcanca admin com o interruptor ligado — verified by `backend/tests/test_notificacoes.py`.
bump-version minor
```
