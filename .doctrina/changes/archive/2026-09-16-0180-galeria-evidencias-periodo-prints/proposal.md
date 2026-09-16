# Change 0180-galeria-evidencias-periodo-prints — galeria de evidencias do periodo com prints e logs dos runs

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** runtime (confident; signals: logs) — opened anyway (--force)
- **Affects specs:** ci-automation

## Why

galeria de evidencias do periodo com prints e logs dos runs

## What

- `ci_ingest.evidencias()`: anexos do período com o contexto do run colado,
  filtráveis por tipo, por repositório de origem e por "só falhas"; devolve
  também o resumo por tipo (que NÃO encolhe com os filtros — ele é o que diz
  o que existe para filtrar) e o total em bytes.
- `GET /ci/evidences?days=&kind=&origin=&failures_only=&limit=`.
- Aba **Evidências** com grade de prints, cartão para os não-imagem, filtros e
  atalho que desce até a execução que produziu a peça.

## Scope boundaries

- A descida (gráfico → execução → job → anexo) continua existindo: a galeria é
  outra entrada para o mesmo arquivo, não a substituição dela.
- Sem visualizador embutido de log: o arquivo abre no navegador, que já sabe
  mostrar texto e imagem melhor do que um leitor improvisado aqui dentro.
- Sem miniatura gerada: o print é servido como está. Gerar thumbnail exigiria
  processar imagem no servidor e duplicar bytes que a retenção já governa.

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
- [x] Verificado no navegador com 96 runs e 432 anexos, a 1440px e 390px: a
      grade monta, os filtros ficam lado a lado, e clicar na execução volta
      para o Painel já com a descida aberta naquele run.

## Open questions

Nenhuma.
