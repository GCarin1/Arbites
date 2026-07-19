---
name: delta-prose-exige-operation-modified
description: Como escrever deltas de spec à mão neste repo sem quebrar os gates — todo delta prose precisa do header `**Operation:** MODIFIED`, o merge na spec é manual (apply só confere), e specs editadas exigem `doctrina validate --fix` para re-sincronizar o index.
when: O agente vai criar/editar um `changes/<id>/specs/<cap>/delta.md`, rodar `doctrina analyze/apply/archive`, ou editar headers de uma spec (Version/Implementation) à mão.
---

# Skill — delta-prose-exige-operation-modified

## When to use this skill

- Escrevendo um `delta.md` novo dentro de uma change (backlog ou
  implementação).
- `doctrina analyze` falhou com "Operation header missing or malformed".
- Editou `**Version:**`/`**Implementation:**` de uma spec e o validate
  reclama de dessincronia com o `index.json`.

## Procedure

1. **Todo delta prose leva o header** logo após o título:
   `**Operation:** MODIFIED` — mesmo quando a capability é nova e o
   conteúdo já foi escrito direto no `spec.md` (o scaffold `spec new` cria
   o arquivo alvo, então `ADDED` é rejeitado pelo apply; use MODIFIED com
   uma nota curta "conteúdo já escrito direto").
2. **O merge é manual.** `doctrina change apply` de delta prose só imprime
   "1 manual" — ele NÃO escreve na spec. Faça o merge com Edit na spec
   alvo (EARS + criteria + bump de Version) ANTES ou DEPOIS do apply, e
   confira com `doctrina analyze` ("ready to apply") e `doctrina coverage`.
3. **Depois de editar spec à mão**, rode `doctrina validate --fix` — o
   Version do arquivo precisa bater com o registrado no `index.json`, e o
   `--fix` re-sincroniza.
4. **Antes do archive**, marque TODOS os checkboxes (tasks.md, incluindo
   closing steps, e Verification do proposal.md) — o archive recusa caixa
   aberta.
5. Em deltas de BACKLOG (change aberta sem implementação), critérios
   entram como `[unverified]` e a numeração final fica para o merge
   ("append — numeração final no merge") — evita conflito quando várias
   changes abertas anexam critérios à mesma spec.

## Anti-patterns

- Delta sem `**Operation:**` → analyze falha na hora do fechamento, não na
  criação (o erro aparece longe da causa).
- Esperar que `change apply` faça o merge do prose — ele não faz; a spec
  fica para trás e o coverage mente.
- Numerar critérios absolutos em duas changes abertas que tocam a mesma
  spec → colisão no merge.
- Editar Version na spec e não rodar `validate --fix` → index dessincroniza.

## Related material

- `AGENTS.md` — "Artifact invariants" (headers, nomes de arquivo, index).
- Exemplo real: change 0077 (falhou o analyze por falta do header; corrigido
  e o padrão baked-in desde 0079).
