# Change 0148-intercambio-arquivo-csv-cucumber — intercambio por arquivo CSV e Cucumber JSON nos dois sentidos, o piso que funciona com qualquer ferramenta sem API

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** integrations

## Why

intercambio por arquivo CSV e Cucumber JSON nos dois sentidos, o piso que funciona com qualquer ferramenta sem API

## What

O adaptador que funciona com **qualquer** ferramenta: import e export por
arquivo, em CSV e Cucumber JSON.

Duas razões, e as duas são fortes:

**1. É a resposta honesta a "independente da ferramenta".** Adaptador por API
só existe onde há API e permissão. Arquivo existe sempre: toda ferramenta de
teste do mercado importa CSV, e o Cucumber JSON já é lido aqui
(`behave_json.py`). Sem credencial, sem MCP, sem pedir nada para a TI.

**2. É o SEGUNDO adaptador — e é ele que valida a porta.** Não existe
abstração antes da segunda implementação: construir a porta com uma
ferramenta na mão produz uma porta com o formato daquela ferramenta. O
adaptador de arquivo é barato e força a porta a ser honesta antes de
qualquer adaptador de API depender dela.

Implementa `ExternalTracker` (0145) declarando capacidades: casos e
resultados sim; evidência como caminho relativo, não como binário embutido;
pasta como coluna. O que não couber é nomeado no preview.

**Afeta spec:** `integrations`. **ADR:** 0015.

## Scope boundaries

- Não tenta adivinhar o dialeto de CSV de cada ferramenta: o mapeamento de
  colunas é configuração, e a IA pode propô-lo (ADR 0015) numa change
  futura — aqui ele é escrito à mão.
- Não empacota evidência binária dentro do CSV.
- Não substitui o import do Xray, que continua sendo migração pontual com
  o seu próprio parser de XML.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Exportar casos e resultados e reimportar o mesmo arquivo não cria
      duplicata — a idempotência vem do vínculo externo (0145).
- [x] O preview nomeia explicitamente que evidência sai como caminho e não
      como anexo.
- [x] Um CSV com coluna faltando falha com mensagem que diz qual, em vez
      de importar pela metade.

## Open questions

Nenhuma.
