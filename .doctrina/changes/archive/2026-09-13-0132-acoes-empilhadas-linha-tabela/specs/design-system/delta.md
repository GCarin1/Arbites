# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

A tabela é a superfície mais importante deste produto — é onde se lê a lista
de defeitos, de casos, de execuções. Medido na tela de Defeitos, com três
registros:

- **Cada linha tem 77px.** Numa tabela que o próprio design-system chama de
  densa, uma linha de 77px cabe menos da metade do que deveria. A culpa é da
  célula de ações: "Editar" e "Excluir" não cabem lado a lado, quebram em
  duas linhas e esticam a linha inteira.
- **A ação destrutiva é o elemento mais chamativo da tela.** "Excluir" em
  vermelho, repetido em toda linha, compete com o conteúdo que a tabela
  existe para mostrar.
- **O identificador quebra em duas linhas.** A coluna de ID tem 66px e
  `DF-0001` vira `DF-` / `0001`. Um identificador que quebra deixa de ser
  identificador.
- **O filtro de opção fica órfão.** O rótulo "Só com lição aprendida" é
  esticado a 285px e a caixa de marcar fica 145px longe do próprio texto —
  parecem dois controles diferentes.

```ops
bump-version minor
append-requirement ubiquitous: The system shall manter a ação destrutiva de uma linha de tabela num menu de ações, para que ela não compita com o conteúdo nem estique a altura da linha.
append-requirement ubiquitous: The system shall impedir que identificador de artefato quebre em mais de uma linha em qualquer listagem.
append-requirement ubiquitous: The system shall manter a caixa de marcar junto do seu rótulo, sem esticar o par pela largura disponível.
append-criterion [unverified] A linha de uma tabela densa não é esticada pelas suas ações, e o identificador nela cabe numa linha só — verified by `frontend/src/styles.css` + `frontend/src/components/Defects.tsx`.
append-criterion [unverified] A caixa de marcar de um filtro fica ao lado do seu rótulo — verified by `frontend/src/styles.css`.
```
