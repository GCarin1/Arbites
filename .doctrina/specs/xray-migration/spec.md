# Spec — xray-migration

**Capability:** xray-migration
**Status:** active
**Implementation:** verified — M2 (backend/arbites/xray_import.py, frontend/src/components/XrayImport.tsx); formato suportado: Jira RSS com custom fields do Xray, adapter isolado com fixture de contrato
**Realizes:** SC4
**Last updated:** 2026-07-04
**Version:** 0.2.0

## Purpose

Ferramenta de migração pontual (não integração contínua) do export XML do
Xray para o formato nativo do Arbites, mais export Markdown. Tem janela de
tempo: o Xray será descomissionado, então este utilitário tem prioridade
acima da automação na ordem de entrega.

## Requirements (EARS)

### Ubiquitous

- The system shall aceitar XML de export do Xray (test repository + testes
  com steps) via `POST /import/xray` retornando um preview.
- The system shall mapear Test → CT `.md` (steps → `## Passos`,
  prerequisites → `## Pré-condições`), labels → tags,
  prioridade → prioridade.
- The system shall gravar a issue key da story (quando presente no XML)
  como `external_key`, deixando ao usuário a decisão de criar a story
  local correspondente na UI de preview.
- The system shall aplicar a importação apenas via
  `POST /import/xray/confirm`, gerando os `.md` no folder escolhido.
- The system shall oferecer `POST /export/markdown?folder=` retornando zip
  dos `.md` (que já são o formato nativo).

### Event-driven

- When o mesmo XML é reimportado, the system shall detectar CTs já
  migrados por `external_key` e pulá-los (idempotência).
- When o preview encontra conflitos de ID ou campos não mapeáveis, the
  system shall listá-los na tabela de preview antes de qualquer escrita.

### State-driven

- While o preview não foi confirmado, the system shall manter o disco
  intocado.

### Unwanted-behavior (must-not)

- The system shall not gravar qualquer arquivo antes da confirmação
  explícita do usuário.
- The system shall not tratar o Xray como integração contínua; é migração
  com prazo.

### Optional

- Where o XML traz campos não mapeáveis, the system may preservá-los como
  nota no corpo do CT para revisão manual.

## Acceptance criteria

1. [verified] Import de XML de amostra gera CTs `.md` corretos no folder
   escolhido — verified by `backend/tests/test_xray_import.py`.
2. [verified] Reimportar o mesmo XML não duplica CTs — verified by
   `backend/tests/test_xray_import.py`.
3. [verified] Preview lista conflitos/skips sem tocar o disco —
   verified by `backend/tests/test_xray_import.py`.

## Maturity

**MVP (committed):**

- Import XML com preview/confirm idempotente; export Markdown zip; wizard
  na UI (upload → preview → confirm).

**Future (aspirational, not committed):**

- Import de execuções históricas do Xray (v1 migra apenas repositório de
  testes).

## Out of scope for this spec

- Integração contínua com Xray/Jira (permanentemente fora de escopo).
