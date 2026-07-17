# Change 0076-execucao-rastreada-ao-vivo-rodar-1-n-feature — Execucao rastreada ao vivo: rodar 1..N .feature (inclusive de features diferentes) cria automaticamente um test execution com todos os CTs lastreados (por tag ou por nome); modal pos-disparo oferece ir ao execution ver o andamento; cards e steps atualizam ao vivo por parsing best-effort do output do behave com o JSON final reconciliando; toast de sucesso ou erro ao terminar; indicador pulsante executando no item Automacao do menu lateral via endpoint leve de runs ativos

- **Status:** proposed
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** local-automation

## Why

Execucao rastreada ao vivo: rodar 1..N .feature (inclusive de features diferentes) cria automaticamente um test execution com todos os CTs lastreados (por tag ou por nome); modal pos-disparo oferece ir ao execution ver o andamento; cards e steps atualizam ao vivo por parsing best-effort do output do behave com o JSON final reconciliando; toast de sucesso ou erro ao terminar; indicador pulsante executando no item Automacao do menu lateral via endpoint leve de runs ativos

## What

Execução rastreada de ponta a ponta:

- `POST /runs/local` aceita `features: list[str]` (1..N arquivos,
  inclusive de features diferentes) — todos entram como posicionais do
  behave; a execution criada inclui TODOS os CTs lastreados dos arquivos
  (por tag OU por nome, via 0075).
- Modal pós-disparo: "Execução EXEC-X criada — ver andamento" com botão
  que navega ao board (Automation ganha onNavigate).
- Live best-effort: o runner parseia o stream plain do behave
  (Scenario/Cenário + linhas de step "passed/failed in") e persiste
  progresso incremental por cenário concluído (save + reindex
  throttled); o board (refresh 5s) mostra os cards andando. O JSON final
  SEMPRE reconcilia (fonte oficial — skill
  progresso-ao-vivo-best-effort-fonte-oficial-corrige).
- `behave_json`/collect casam resultado→CT também por nome de cenário
  (name_map do target), não só por tag.
- Fim do run: toast sucesso/erro (SSE done já entrega o status).
- Indicador no menu: `GET /runs/active` (contagem de runs
  queued/running); o App consulta no refresh (5s) e o item Automação
  ganha dot pulsante enquanto ativo.

## Scope boundaries

Parsing ao vivo é best-effort declarado (EN/PT keywords do plain
format); qualquer divergência é corrigida pelo JSON final. Depende da
0075 para o vínculo por nome. Não altera o disparo remoto GitHub.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
