# Change 0154-modelo-sinal-generico-manifesto — modelo de sinal generico e manifesto no artifact, para o workflow declarar o que produziu sem o arbites conhecer cada tipo

- **Status:** proposed
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain; signals: declarar)
- **Affects specs:** local-automation

## Why

modelo de sinal generico e manifesto no artifact, para o workflow declarar o que produziu sem o arbites conhecer cada tipo

## What

O artifact do pipeline traz muito mais que resultado de teste: telemetria,
logs, acessibilidade, prints, e uma análise de IA em Markdown. A ADR 0006
fixou a coleta em UM formato (Cucumber JSON), e telemetria não cabe nele.

**Sinal genérico, não um schema por tipo** (ADR 0016):

```
signal: { run_id, kind, name, value, unit, at }
```

Acessibilidade vira `kind=a11y, name=violations.critical, value=3`;
telemetria vira `kind=telemetry, name=lcp_ms, value=2400, unit=ms`. O Arbites
**não conhece** "acessibilidade" nem "lighthouse" — se conhecesse, cada sinal
novo viraria código novo e o pipeline deixaria de poder evoluir sozinho.

**O que não é número é ANEXO, não sinal.** Print, log e o `.md` da análise se
leem, não se plotam. Eles ficam presos à run, hasheados como as evidências já
são hoje.

**Quem produz declara, por manifesto.** Um `arbites.json` dentro do artifact
diz quais sinais tem e onde. Convenção de nome de arquivo acopla os dois
lados e quebra em silêncio quando alguém renomeia — ela fica como *fallback*
anunciado, para o caso de o workflow não poder ser alterado.

O Cucumber JSON passa a ser um sinal entre outros, com o mesmo parser.

## Scope boundaries

- Não muda o parser de Cucumber JSON: ele continua sendo o que lê resultado.
- Não interpreta a semântica do sinal: o Arbites não sabe se `lcp_ms` maior é
  pior. Direção e meta são configuração de quem instala.
- Não desenha gráfico (change 0155).

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
- [ ] Um artifact com manifesto produz sinais consultáveis por nome e
      período, sem o Arbites conhecer o tipo de antemão.
- [ ] Um sinal novo, nunca visto, é ingerido sem mudança de código.
- [ ] Print, log e `.md` chegam como anexo da run, hasheados, e não como
      sinal.
- [ ] Artifact sem manifesto cai no modo convenção e **diz** que caiu.

## Open questions

Nenhuma.
