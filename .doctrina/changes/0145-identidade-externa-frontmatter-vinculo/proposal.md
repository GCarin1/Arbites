# Change 0145-identidade-externa-frontmatter-vinculo — identidade externa no frontmatter e vinculo por sistema, a base para nao duplicar o que ja existe na ferramenta oficial

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** integrations

## Why

identidade externa no frontmatter e vinculo por sistema, a base para nao duplicar o que ja existe na ferramenta oficial

## What

Abre a capability `integrations` e entrega o seu alicerce: **saber o que
daqui já está lá**.

Hoje existe `external_key`: um campo de texto, único, sem sistema, sem
revisão e sem validação — a própria ADR 0007 registrou isso como consequência
negativa aceita. Ele serve para um humano clicar, não para uma máquina
decidir. Com ele não dá para responder as duas perguntas que tornam qualquer
escrita idempotente: *"isto já foi criado lá?"* e *"mudou desde a última
vez?"*.

O vínculo passa a viver no frontmatter, um por sistema:

```yaml
external:
  - system: businessmap
    id: "CARD-4821"
    revision: "17"          # o que o remoto tinha na última sincronia
    synced_hash: "a3f01e…"  # o que NÓS tínhamos naquele momento
    synced_at: "2026-09-13T19:40:00Z"
```

No arquivo e não só no índice, porque o índice é descartável (ADR 0001) e o
vínculo não pode morrer num reindex. Em lista e não em campo único, porque
uma migração corporativa tem os dois sistemas vivos ao mesmo tempo.

`synced_hash` é a peça que faz o resto funcionar: com ele, "mudou dos dois
lados desde a última sincronia" é uma comparação, não um palpite — e é o que
transforma sobrescrita silenciosa em **conflito registrado**.

Entrega também a porta `ExternalTracker` com **capacidades declaradas** (ADR
0015) e as consultas `external_links` / `unsynced`, que são o que o agente
MCP vai consumir na change 0146.

**Afeta spec:** `integrations` (nova). **ADR:** 0015.

## Scope boundaries

- Não transporta nada: nenhum adaptador, nenhuma chamada a sistema externo.
  Esta change só sabe REGISTRAR e COMPARAR vínculos.
- Não remove `external_key`: ele continua valendo como referência textual
  para quem só quer um link clicável. O vínculo estruturado é outro campo.
- Não desenha a tela de conflito em Problemas — aqui o conflito é apenas
  detectado e registrado; a apresentação vem depois.
- Não toca em credencial: nada aqui autentica em lugar nenhum.

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
- [ ] O vínculo sobrevive a `reindex_full` — o teste apaga o índice e
      relê do arquivo.
- [ ] Dois sistemas no mesmo artefato, e a consulta por sistema não vaza o
      vínculo do outro.
- [ ] Editar artefato sincronizado o coloca em `unsynced`; sincronizar de
      novo o tira.
- [ ] Mudança dos dois lados vira conflito, e nenhum lado é sobrescrito.

## Open questions

Nenhuma.
