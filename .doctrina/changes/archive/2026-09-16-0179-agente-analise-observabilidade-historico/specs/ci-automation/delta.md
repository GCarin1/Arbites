# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

---

O painel responde perguntas isoladas e ninguém junta as três no fim do dia. E
"melhorou desde o mês passado?" não é uma pergunta que gráfico nenhum
responde, porque exige comparar dois momentos inteiros.

```ops
append-requirement event: When uma análise da observabilidade é pedida, the system shall montar o dossiê do período — saúde, sinais com meta e direção, instabilidade, achados de acessibilidade e os recortes por repositório de teste e de origem — e gravá-la como artefato do workspace junto com esse dossiê.
append-requirement ubiquitous: The system shall manter o histórico das análises lido do disco, de modo que reconstruir o índice não apague o registro que justifica uma decisão técnica.
append-requirement event: When duas análises são comparadas, the system shall entregar os dois dossiês e os dois vereditos ao modelo, ordenados da mais antiga para a mais recente, em vez de calcular melhora no código.
append-requirement unwanted: The system shall not analisar um período sem execução ingerida; recusa dizendo que não há o que analisar, em vez de devolver um veredito sobre o vazio.
append-criterion [verified] O dossiê é recorte e não cópia do painel, marca o sinal sem direção declarada e destaca a instabilidade nova; a análise vira arquivo com o dossiê junto e sobrevive a um reindex; duas análises no mesmo dia não colidem; identificador com travessia de caminho é recusado; e o comparativo vai sempre da mais antiga para a mais recente, com os números das duas — verified by `backend/tests/test_analise_observabilidade.py`.
set-header Last updated: 2026-09-16
bump-version minor
```
