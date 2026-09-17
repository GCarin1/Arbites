# Change 0186-bundle-ca-apontado-mas — bundle de CA apontado mas ilegivel manda declarar a variavel que ja foi declarada

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** product (confident; signals: declarar)
- **Affects specs:** ci-automation

## Why

bundle de CA apontado mas ilegivel manda declarar a variavel que ja foi declarada

## What

- `tls.py`: `apontado()` (a variável DECLARADA, use-se ou não) separada de
  `ca_bundle()` (a que dá para usar). `problema_do_bundle()` nomeia o motivo:
  não existe, é pasta, ou não carrega como bundle — este último via
  `ssl.load_verify_locations`, porque existir não basta.
- `explicacao()` passa a ter TRÊS ramos. O que faltava era o do meio:
  declarado e quebrado, que caía no ramo "não declarado" e mandava declarar
  de novo.
- `aviso()` e `linha_do_arranque()`: o problema aparece no terminal e na aba
  Problemas sem ninguém disparar chamada externa.

## Scope boundaries

- Bundle quebrado continua caindo no padrão em vez de derrubar a chamada: o
  `IOError` do httpx não diz nada a quem está olhando. O que mudou é que a
  queda deixou de ser calada.
- Continua sem ler o truststore do sistema operacional. Adivinhar em quem
  confiar é a decisão que não cabe ao programa tomar em silêncio (ADR 0183).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met
- [x] O caminho exato do relato foi usado como caso de teste. and cite their evidence (`doctrina coverage`).

## Open questions

Nenhuma.
