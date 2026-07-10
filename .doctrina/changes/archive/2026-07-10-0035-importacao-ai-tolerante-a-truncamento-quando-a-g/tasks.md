# Tasks — Change 0035

- [x] `_all_objects`: varre todo `{…}` (inclusive aninhado) p/ achar CTs íntegros.
- [x] `_salvage_import`: monta ImportConversion parcial; recupera folder do cabeçalho.
- [x] `complete(..., salvage=...)`: usa salvamento quando nenhum objeto completo valida.
- [x] `convert_import` passa `salvage=_salvage_import`.
- [x] Testes de truncamento (unit + end-to-end) + suíte verde + build.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder.
- [x] Update `.doctrina/index.json`.
