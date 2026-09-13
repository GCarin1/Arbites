# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer a escolha de arquivo pelo mesmo botao dos demais controles, com o nome do arquivo escolhido visivel e a possibilidade de reescolher o mesmo arquivo, sem expor o controle nativo do sistema operacional em nenhuma tela.
append-requirement ubiquitous: The system shall manter o texto de um passo de execucao numa faixa propria em tela estreita, com as acoes e o status do passo na faixa seguinte, em vez de espremer o texto numa coluna ao lado dos botoes e deixar o status orfao numa terceira linha.
append-criterion [unverified] Nenhuma tela exibe o controle de arquivo nativo — os quatro pontos de envio passam pelo botao do sistema, mostram o nome escolhido e aceitam reescolher o mesmo arquivo — verified by `frontend/src/components/FilePicker.tsx`.
append-criterion [unverified] Em 390 px a linha de um passo de execucao cai em duas faixas (numero e texto; acoes e status) e em 1440 px continua numa faixa so — verified by `frontend/src/styles.css` + `frontend/src/components/Executions.tsx`.
bump-version minor
```
