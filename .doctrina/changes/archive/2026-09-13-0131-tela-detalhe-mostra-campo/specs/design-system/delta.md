# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

A tela de detalhe — a que responde "o que é este caso, este requisito, este
defeito" — tem dois problemas, e o primeiro é um defeito de layout medido.

**Campo vazio com a altura do campo mais alto.** A grade de metadados estica
todos os campos de uma linha até a altura do maior. Medido no caso de teste:
"Arquivo" tem um caminho de duas linhas e ocupa 139px, e por causa dele
"Critérios EARS", "Squad" e "Tags" — todos vazios — também ocupam **139px
cada**, com um travessão flutuando no meio de um espaço em branco. Três
campos sem conteúdo tomam mais da metade do card.

**A ação destrutiva ao lado da principal.** "Excluir" fica encostado em
"Editar", mesmo tamanho, mesma linha. Numa tela que se abre para ler, a
ação que apaga o trabalho não deveria estar a um erro de mira da ação que
se usa todo dia. Ela não precisa sumir — precisa sair do caminho.

```ops
bump-version minor
append-requirement ubiquitous: The system shall dimensionar cada campo de metadado pelo próprio conteúdo, sem esticá-lo até a altura do campo mais alto da mesma linha.
append-requirement ubiquitous: The system shall separar a ação destrutiva da ação principal numa tela de detalhe, recolhendo-a num menu de ações em vez de deixá-la a um erro de mira.
append-criterion [unverified] Um campo de metadado vazio ocupa a altura de uma linha, e não a do campo mais alto ao lado dele — verified by `frontend/src/styles.css`.
append-criterion [unverified] A ação destrutiva de uma tela de detalhe fica num menu de ações, alcançável pelo teclado e fechando com Esc — verified by `frontend/src/components/OverflowMenu.tsx`.
```
