# Change 0067-fix-automacao-target-salvo-com-feature — fix automacao: target salvo com .feature encontrados no browse, mas o dropdown de features fica vazio e o run devolve 422 empty_selection quando os cenarios do repositorio NAO tem tags @CT-XXXX. Causa: o preview (browse-features) lista do disco via glob, mas o dropdown pos-save (GET /targets/name/features) e a resolucao do run leem da tabela scenarios, que o scan_target so popula com cenarios tagueados @CT-\d+ — duas fontes divergentes para a mesma lista. Corrigir: dropdown deve listar as features reais do glob mesmo sem tags; rodar um .feature inteiro deve funcionar sem CTs mapeados (execution sem vinculo ou com resultado nao-mapeado explicito); quando nao ha cenarios tagueados, a UI explica o porque em vez de mostrar vazio. Bug irmao: prefixo CT hardcoded na regex _CT_TAG_RE apesar de id_prefixes.testcase ser configuravel.

- **Status:** proposed
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** local-automation

## Why

fix automacao: target salvo com .feature encontrados no browse, mas o dropdown de features fica vazio e o run devolve 422 empty_selection quando os cenarios do repositorio NAO tem tags @CT-XXXX. Causa: o preview (browse-features) lista do disco via glob, mas o dropdown pos-save (GET /targets/name/features) e a resolucao do run leem da tabela scenarios, que o scan_target so popula com cenarios tagueados @CT-\d+ — duas fontes divergentes para a mesma lista. Corrigir: dropdown deve listar as features reais do glob mesmo sem tags; rodar um .feature inteiro deve funcionar sem CTs mapeados (execution sem vinculo ou com resultado nao-mapeado explicito); quando nao ha cenarios tagueados, a UI explica o porque em vez de mostrar vazio. Bug irmao: prefixo CT hardcoded na regex _CT_TAG_RE apesar de id_prefixes.testcase ser configuravel.

## What

**Reprodução** (real, em repositório de testes existente sem convenções
Arbites): configurar target → "Procurar .feature" lista os arquivos
corretamente → salvar → o select de feature do run fica vazio → disparar o
run devolve `422 empty_selection`.

**Diagnóstico** (código, não hipótese):

- O preview (`GET /automation/browse-features` →
  `gherkin_scan.list_feature_files`) lista TODO `.feature` que o glob
  resolve, direto do disco, sem exigir tag.
- O dropdown pós-save (`GET /targets/{name}/features`, `api.py`) lê da
  tabela `scenarios` — que `scan_target` só popula com cenários cuja tag
  casa `_CT_TAG_RE = ^@(CT-\d+)$` (`gherkin_scan.py`). Repositório sem tags
  `@CT-XXXX` → zero linhas → dropdown vazio.
- O run (`create_local_run`) resolve os CTs da feature pela MESMA tabela
  vazia → `422 empty_selection` ("informe testcase_ids, tags ou feature que
  resolvam para CTs").
- Encoding do caminho (acentos/vírgulas/espaços/pasta sincronizada na
  nuvem) foi DESCARTADO:
  o browse funciona com o mesmo caminho; `URLSearchParams` encoda correto.

**Correções propostas:**

1. `GET /targets/{name}/features` passa a listar as features reais do glob
   (reutilizando `list_feature_files` com o `local_path`/`features_glob` do
   target salvo), anotando por arquivo quantos cenários estão mapeados
   (`@CT`) e quantos não — o dropdown nunca mais fica vazio se o disco tem
   features.
2. Rodar um `.feature` inteiro sem cenários mapeados passa a ser permitido:
   a execution é criada sem CTs vinculados (ou com um resultado
   "não mapeado" explícito), rodando `behave <arquivo>.feature` normalmente
   — o vínculo CT↔cenário (ADR 0003) continua sendo o caminho para
   rastreabilidade, mas deixa de ser pré-requisito para EXECUTAR.
3. UX: quando não há cenários tagueados, a UI explica ("N cenários sem tag
   @CT — tague para rastreabilidade ou rode o arquivo inteiro") em vez de
   mostrar um select vazio sem contexto.
4. Bug irmão: `_CT_TAG_RE` hardcoda o prefixo `CT` apesar de
   `id_prefixes.testcase` ser configurável — derivar a regex do prefixo
   configurado (mesma família da change 0059/risk-map; skill
   `novo-consumidor-repassa-config-do-helper`).

## Scope boundaries

Não muda o ADR 0003 (vínculo CT↔cenário por tag continua sendo o modelo de
rastreabilidade) — só deixa de bloquear a execução quando o vínculo não
existe. Não altera o runner (`runner.py` já suporta rodar por arquivo).
Não mexe no disparo remoto GitHub (`ci-automation`). Nenhum caminho real de
usuário/empresa entra em código, teste ou doc — reproduzir com repositório
sintético em tmp_path (caminho com espaços/acentos/vírgulas para cobrir
também a robustez de path, já que é barato incluir no fixture).

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
