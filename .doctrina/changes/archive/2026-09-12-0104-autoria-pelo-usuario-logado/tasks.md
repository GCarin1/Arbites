# Tasks — Change 0104-autoria-pelo-usuario-logado

- [x] `api.py`: `_profile_path` por conta (`profiles/<slug>.md`), com o `profile.md` da raiz como fallback quando a autenticação está desligada.
- [x] `api.py`: herança única do `profile.md` da raiz pela conta de menor id.
- [x] `api.py`: `owner` da execution vem da sessão, ignorando o que o corpo mandar.
- [x] `api.py`: `created_by` no frontmatter de requisito, caso de teste e defeito na criação, preservado nas edições.
- [x] `backend/tests/test_authorship.py` cobrindo os 5 critérios.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0104-autoria-pelo-usuario-logado/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
