# Tasks — Change 0050 (chore)

- [x] Remover o `<div className="panel">` (12 blocos `panel-hint`, um por aba) de `App.tsx`.
- [x] Sidebar fica só com `<nav className="nav">`.
- [x] CSS: remover `.sidebar .panel`/`.sidebar .panel-hint` (órfãos); `.sidebar .nav` ganha `flex:1; min-height:0` (preenche o espaço; antes tinha `max-height:60vh` + `border-bottom` para dar lugar ao painel).
- [x] Build frontend verde; zero referências restantes a `panel-hint`/`className="panel"`.

## Closing steps

- [x] Apply (chore, zero deltas).
- [x] Archive.
- [x] Update index.json.
