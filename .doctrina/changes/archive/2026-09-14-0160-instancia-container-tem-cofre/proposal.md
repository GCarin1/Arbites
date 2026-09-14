# Change 0160-instancia-container-tem-cofre — instancia em container nao tem cofre do SO: a ausencia de keyring derrubava a aplicacao inteira com 500, e a credencial de CI nao tinha como ser configurada

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** runtime (confident; signals: ci) — opened anyway (--force)
- **Affects specs:** ci-automation

## Why

instancia em container nao tem cofre do SO: a ausencia de keyring derrubava a aplicacao inteira com 500, e a credencial de CI nao tinha como ser configurada

## What

**Incidente.** Num container, `docker compose up` subia e a aplicação
devolvia **500 em toda navegação**: `GET /api/v1/warnings` explodia com
`keyring.errors.NoKeyringError`.

A causa é minha, e recente. A change 0157 fez a tela Problemas compor o estado
da credencial de CI — e essa tela carrega em todo carregamento de página. Numa
imagem Docker enxuta não existe keychain nenhum, então a pergunta "há
credencial?" levantava exceção. **Uma funcionalidade de CI derrubou a
navegação inteira** porque assumiu que o cofre do SO sempre existe.

`GET /settings/github/token` já quebrava do mesmo jeito antes da 0157 — só não
doía, porque aquela tela fica no fundo de Automação. A 0157 arrastou a mesma
armadilha para uma rota que todo mundo passa.

Duas correções, e as duas são a mesma ideia:

1. **Ausência de cofre é RESPOSTA, não acidente.** Ler devolve "não há
   credencial". Guardar recusa com `409` e a saída escrita. A falta aparece na
   tela Problemas com o remédio — em vez de um campo que recusa em silêncio
   quando alguém finalmente tenta usá-lo.
2. **Existe uma saída real no container** (ADR 0017): `ARBITES_GITHUB_TOKEN`
   no ambiente do processo, com precedência sobre o cofre. Sem isso eu estaria
   publicando um `docker-compose.yml` onde metade do produto não liga.

**De quebra:** a aba Observabilidade estava sem ícone desde a change 0155. O
fallback de ícone ausente era um `<span>` vazio — invisível, nada quebrava, só
sumia. Agora ele desenha um traço neutro, então a próxima ausência aparece.

## Scope boundaries

- Não muda a ADR 0008 para o desktop: lá o cofre do SO continua sendo o lugar,
  e o comportamento é idêntico ao de antes.
- Não guarda segredo em arquivo do workspace, que é o que a 0008 rejeitou e
  continua rejeitado.

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
- [x] A regressão exata: `/warnings` responde 200 numa instância sem cofre.
- [x] A falta de cofre aparece como problema, com o remédio e o nome da
      variável.
- [x] Guardar token sem cofre recusa com 409 explicando, não 500.
- [x] Credencial pelo ambiente funciona, e o ambiente ganha do cofre.
- [x] O valor do token nunca volta em resposta nem toca o disco do workspace.
- [x] Com cofre, o comportamento é o de sempre.

## Open questions

**A lição, para não repetir:** o teste que faltava não era de keyring — era de
**ambiente de execução**. A suíte roda com um backend de keyring instalado, e
por isso nunca viu o que o container vê. Rota que carrega em toda navegação
não pode depender de recurso opcional do host; se depender, precisa de um
teste que simule a ausência dele. É o que `test_sem_cofre.py` passa a fazer.

<!-- List unresolved decisions. Empty if none. -->
