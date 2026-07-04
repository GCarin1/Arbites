# Design — Change 0004-m2-migracao-xray-import-xml-com-preview-e-confir

## Approach

O parser é um **adapter isolado** (`xray_import.py`) que converte o XML de
export (Jira RSS com custom fields do Xray — "Manual Test Steps" como JSON
embutido, prioridade, labels, issuelinks) num modelo neutro `XrayTest`.
Todo o resto do fluxo (preview, confirm, escrita de `.md`) opera sobre o
modelo neutro — se o export real da B3 variar, só o adapter muda, e os
XMLs de exemplo versionados em `backend/tests/fixtures/` são o contrato.

O fluxo em duas etapas é **stateless**: o preview parseia e responde sem
tocar o disco; o confirm recebe o mesmo XML de novo (multipart) + opções
(folder, stories a criar) e re-parseia. Sem estado de sessão no servidor —
consistente com single-user local e elimina a classe de bug "preview
expirado".

Idempotência por `external_key`: nova coluna no índice de testcases
(populada do frontmatter); no confirm, cada test cujo `external_key` já
existe no índice é pulado. Migração de schema: `ALTER TABLE ... ADD
COLUMN` tolerante em `connect()` (o banco é descartável; isso só evita
exigir reindex manual em índices existentes).

## Alternatives considered

- Estado de preview no servidor (token) — rejeitado: estado volátil sem
  benefício num app single-user; re-parse é barato.
- Suportar múltiplos formatos de export desde já — rejeitado: YAGNI; o
  adapter isola a mudança quando o XML real chegar.

## Trade-offs and risks

- O formato exato do export da B3 pode divergir da fixture — mitigado
  pelo adapter + testes de contrato (ajuste localizado).
- Steps do Xray com HTML embutido são normalizados para texto simples;
  formatação rica se perde (aceito para migração).

## Decisions to record as ADRs

Nenhuma nova — executa o ADR 0007 (Xray como migração pontual).
