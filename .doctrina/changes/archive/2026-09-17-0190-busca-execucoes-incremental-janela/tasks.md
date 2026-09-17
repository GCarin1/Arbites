# Tasks — Change 0190-busca-execucoes-incremental-janela

- [x] `ci_cobertura.py`: intervalos por origem, `fundir()` e `lacunas()`.
- [x] `ingerir()` por janela, varrendo só a lacuna.
- [x] `_pendentes()` para pela data; filtro `created` no cliente do provedor.
- [x] Margem de 48h fora da cobertura.
- [x] `days`/`refresh` na rota; o período da tela vai junto.
- [x] Botão "Reconferir período" na aba Configuração.
- [x] `backend/tests/test_busca_incremental.py`.
- [x] README: como a busca incremental se comporta.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-17-0190-busca-execucoes-incremental-janela/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
