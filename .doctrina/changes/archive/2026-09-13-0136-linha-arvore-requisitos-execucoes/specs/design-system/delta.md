# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

```ops
append-requirement ubiquitous: The system shall impedir que os rotulos de uma linha de arvore se desenhem uns sobre os outros quando falta largura — so o elemento que recorta com reticencias cede espaco, e em tela estreita os metadados descem para uma segunda linha em vez de espremer o titulo.
append-criterion [unverified] Em 390 px nenhuma caixa de texto de uma linha das arvores de requisitos e de execucoes se sobrepoe a vizinha, o identificador aparece inteiro, e em 1440 px cada item continua numa linha so — verified by `frontend/src/styles.css`.
bump-version minor
```
