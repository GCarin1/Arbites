# Change 0004-m2-migracao-xray-import-xml-com-preview-e-confir — M2 - migracao Xray: import XML com preview e confirmacao idempotente, export Markdown zip

- **Status:** proposed
- **Date:** 2026-07-04
- **Owner:** Gcarini
- **Affects specs:** xray-migration, testcases

## Why

M2 é uma ferramenta de migração com prazo (ADR 0007): o Xray será
descomissionado e a base de testes da B3 precisa ser resgatada enquanto há
acesso. Posicionado antes da automação na ordem de entrega exatamente para
proteger essa janela. Critério de pronto = SC4.

## What

- `backend/arbites/xray_import.py` — adapter de parsing do XML de export
  do Xray (formato Jira RSS com custom fields do Xray), isolado atrás de
  interface própria e testado por contrato com XMLs de exemplo
  versionados em `backend/tests/fixtures/` (risco "formato mudar" do
  intake §17).
- Mapeamento: Test → CT `.md` (steps → `## Passos`, per-step expected →
  `## Resultado esperado`, prerequisites → `## Pré-condições`),
  labels → tags, prioridade Jira → prioridade CT, issue key → `external_key`.
- Fluxo em duas etapas stateless: `POST /import/xray` (multipart →
  preview, disco intocado) e `POST /import/xray/confirm` (re-envia o XML +
  opções: folder de destino e criação de stories locais a partir das
  issue keys vinculadas).
- Idempotência: CTs já migrados são detectados por `external_key`
  (nova coluna no índice de testcases) e pulados no reimport.
- `POST /export/markdown?folder=` — zip dos `.md` (formato nativo).
- Frontend: wizard na aba Migração (upload → preview em tabela → escolha
  de folder/stories → confirm → resultado).
- Testes: `backend/tests/test_xray_import.py` (mapeamento, idempotência,
  preview sem escrita, export zip) sobre fixture versionada.

## Scope boundaries

- Import de execuções históricas do Xray fica fora (Future da spec; v1
  migra o repositório de testes).
- Nenhuma integração contínua com Xray/Jira (ADR 0007 — permanente).
- O adapter suporta o formato Jira RSS/XML com steps do Xray; variações
  do export real da B3 entram como ajuste no adapter (isolado), não no
  fluxo.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

- O formato exato do export da B3 só será conhecido com um XML real; o
  adapter isolado + testes de contrato limitam o ajuste a um único módulo.
