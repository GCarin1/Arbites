# Spec Delta — capability: ci-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ci-automation/spec.md`

```ops
bump-version minor
append-requirement event: When uma execução é gravada, the system shall calcular as medidas que já apurou sobre ela — duração, veredito, jobs falhos, cenários e sua taxa, violações de acessibilidade por gravidade e critérios WCAG distintos —, emitindo-as como sinais marcados com a origem derivada.
append-requirement ubiquitous: The system shall carregar a origem de cada sinal — declarado pelo produtor ou derivado pelo Arbites — em toda leitura da série, até a tela.
append-requirement unwanted: The system shall not emitir medida derivada cujo nome já tenha sido declarado no manifesto, nem medida cuja fonte não exista na execução; um zero inventado é um ponto no gráfico afirmando o que não foi medido.
append-requirement unwanted: The system shall not derivar sinal de arquivo cuja forma não reconhece; reconhecer um formato documentado é leitura, adivinhar o significado de um número solto é invenção.
append-criterion [verified] Sem nenhum manifesto a série existe, com duração vinda dos horários do provedor, cenários do relatório e acessibilidade dos achados; cancelada não vira zero; nome declarado desliga o derivado homônimo; ausência de fonte não vira sinal; toda medida carrega a origem até o painel; e reprocessar do disco cria a série do que já estava ingerido — verified by `backend/tests/test_sinais_derivados.py`.
```
