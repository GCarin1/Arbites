# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

O Kanban é bom para arrastar e ver o todo, e ruim para o que o QA faz na
maior parte do tempo: sentar e executar vinte casos em sequência. Cada caso
hoje custa abrir o modal, marcar, anexar, fechar o modal, procurar o próximo
— cinco gestos de navegação para um de trabalho.

O modo guiado troca isso por três painéis lado a lado: os ciclos à esquerda,
os casos do ciclo no meio e o caso ativo à direita, com passos marcáveis,
evidência e resultado no mesmo lugar. O rodapé avança para o próximo caso sem
sair da tela, que é o gesto que faz uma regressão inteira caber numa sessão.

O Kanban não sai: os dois modos leem e escrevem a mesma execution, e a
escolha entre eles é do QA, não do produto.

```ops
bump-version minor
append-requirement ubiquitous: The system shall oferecer, ao lado do Kanban, um modo guiado em três painéis — ciclos, casos do ciclo e caso ativo — operando sobre a mesma execution, sem nenhum endpoint novo.
append-requirement ubiquitous: The system shall permitir no painel do caso ativo marcar cada passo, anexar evidência, escrever comentário e dar o resultado, sem abrir modal e sem sair da tela.
append-requirement ubiquitous: The system shall exibir no rodapé do modo guiado a posição do caso ativo no ciclo, o avanço para o próximo caso e o atalho que dá resultado e avança num gesto só.
append-requirement event: When o resultado do caso ativo é registrado no modo guiado, the system shall avançar para o próximo caso ainda pendente do ciclo, e parar no último em vez de voltar ao começo.
append-requirement unwanted: The system shall not substituir o Kanban pelo modo guiado; os dois modos leem e escrevem a mesma execution e a escolha é de quem executa.
append-criterion [unverified] O modo guiado percorre os casos de um ciclo na ordem, dá resultado e avança sem sair da tela, e o que ele grava é a mesma execution que o Kanban lê — verified by `backend/tests/test_executions_guided.py`.
append-criterion [unverified] Dar resultado no último caso pendente encerra a fila em vez de voltar ao começo, e um ciclo fechado é percorrível mas não gravável — verified by `backend/tests/test_executions_guided.py`.
```
