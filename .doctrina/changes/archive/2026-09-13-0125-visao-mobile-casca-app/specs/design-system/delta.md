# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

A casca do app é desktop inteira: cabeçalho de 56 px numa linha só, com
marca, contadores do workspace, busca, caminho do workspace e reindexar; e
barra lateral de 240 px fixa ao lado do conteúdo. Num celular de 390 px a
lateral come 240 e sobram 150 para o produto — não é "apertado", é
inutilizável. O cabeçalho, na mesma largura, transborda.

O alvo não é um app separado. É a mesma tela sabendo se encolher:

- **A lateral vira gaveta.** Abaixo do ponto de quebra ela sai do fluxo e é
  aberta por um botão no cabeçalho, fechando ao navegar, no toque fora e no
  Esc — os três, porque num celular o gesto de fechar varia e nenhum deles é
  o óbvio para todo mundo.
- **O cabeçalho fica com o essencial.** Marca, busca e conta continuam;
  contadores do workspace, caminho do diretório e reindexar somem, porque
  são informação de quem administra a instância sentado numa mesa, não de
  quem abre o celular para ver como está a regressão.
- **O que é largo rola em vez de espremer.** O Kanban tem seis colunas: numa
  tela estreita, espremê-las torna todas ilegíveis ao mesmo tempo. Rolagem
  horizontal com encaixe preserva uma coluna inteira e legível por vez.
- **O alvo de toque cresce.** Item de menu e ação de linha passam a ter
  altura de toque confortável; o mesmo pixel que sobra num mouse falta num
  polegar.

```ops
bump-version minor
append-requirement ubiquitous: The system shall apresentar a mesma interface em tela estreita com a barra lateral fora do fluxo, aberta por um controle no cabeçalho e fechada ao navegar, ao tocar fora e pelo Esc.
append-requirement ubiquitous: The system shall reduzir o cabeçalho em tela estreita ao essencial — marca, busca e conta —, escondendo contadores do workspace, caminho do diretório e reindexar, que são controles de quem administra a instância.
append-requirement ubiquitous: The system shall dar rolagem horizontal com encaixe por coluna ao Kanban em tela estreita, em vez de espremer as seis colunas na largura disponível.
append-requirement ubiquitous: The system shall garantir alvo de toque de no mínimo 44 px de altura nos itens de navegação e nas ações de linha quando o ponteiro for grosseiro.
append-requirement state: While a gaveta de navegação está aberta, the system shall impedir a rolagem do conteúdo atrás dela e devolver o foco ao controle que a abriu quando ela fechar.
append-requirement unwanted: The system shall not servir uma interface reduzida em funcionalidade na tela estreita; o que muda é a forma, e nenhuma tela deixa de ser alcançável.
append-criterion [unverified] A casca declara o ponto de quebra, a gaveta e o cabeçalho enxuto, e nenhuma tela fica inalcançável em largura de celular — verified by `frontend/src/App.tsx` + `frontend/src/styles.css`.
append-criterion [unverified] Nenhuma tela em largura de 390 px transborda horizontalmente, e o que é largo por natureza rola dentro do próprio bloco — verified by `frontend/src/styles.css`.
```
