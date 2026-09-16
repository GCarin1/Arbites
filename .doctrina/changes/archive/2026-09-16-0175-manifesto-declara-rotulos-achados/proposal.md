# Change 0175-manifesto-declara-rotulos-achados — manifesto declara rotulos e achados estruturados de acessibilidade, com leitor nativo de axe

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** ci-automation

## Why

manifesto declara rotulos e achados estruturados de acessibilidade, com leitor nativo de axe

## What

- `backend/arbites/ci_axe.py` (novo): leitor do JSON do axe-core → achados
  com regra, gravidade, critério da WCAG (da tag `wcag143` → `1.4.3`), nível,
  quantidade de **elementos**, página e link de ajuda. Aceita uma página
  (objeto) e várias (lista), que é o que uma varredura de micro-frontends
  produz. `normalizar_achados` dá a mesma forma ao que vem declarado.
- `backend/arbites/ci_ingest.py`: manifesto v2 (`labels` + `findings`), com a
  v1 ainda aceita; `normalizar_rotulos`, `extrair_achados`; agregações
  `distribuicao`, `achados`, `por_repositorio`, `por_rotulo`,
  `nomes_de_rotulo`; e tudo isso no `painel`.
- `backend/arbites/indexer.py`: tabelas `ci_findings` e `ci_labels`.

## Scope boundaries

- O Arbites continua sem semântica própria: ele não sabe que `lcp_ms` maior é
  pior nem qual componente importa mais. Direção, meta e topologia seguem
  sendo declaração de quem instala (ADR 0016).
- Sem correlação automática entre repositório de deploy e componente: o
  vínculo é o rótulo declarado, porque adivinhar topologia de micro-frontend
  pelo nome do repositório erra na primeira exceção.

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

## Open questions

Nenhuma.
