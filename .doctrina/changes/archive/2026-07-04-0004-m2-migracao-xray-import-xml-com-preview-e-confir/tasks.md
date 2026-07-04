# Tasks — Change 0004-m2-migracao-xray-import-xml-com-preview-e-confir

- [x] Backend: coluna `external_key` em testcases (schema + insert +
      migração tolerante em connect).
- [x] Backend: `xray_import.py` — parser XML → modelo neutro `XrayTest`
      (steps, prerequisites, labels, prioridade, story key).
- [x] Backend: preview (sem escrita) com status new/exists e campos não
      mapeáveis; confirm idempotente gerando `.md` + stories opcionais.
- [x] Backend: `POST /import/xray`, `POST /import/xray/confirm`,
      `POST /export/markdown?folder=` (zip).
- [x] Backend: fixture XML versionada + `test_xray_import.py`
      (mapeamento, idempotência, preview intocado, export zip).
- [x] Frontend: aba Migração — wizard upload → preview → confirm.
- [x] Deltas: xray-migration → verified; testcases → external_key no
      frontmatter/índice.
- [x] `doctrina analyze` limpo e `doctrina verify` verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-04-0004-m2-migracao-xray-import-xml-com-preview-e-confir/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
