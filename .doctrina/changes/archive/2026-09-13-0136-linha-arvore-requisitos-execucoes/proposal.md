# Change 0136-linha-arvore-requisitos-execucoes — linha de arvore de requisitos e de execucoes desenha os rotulos uns por cima dos outros em 390px: id, cobertura, status e data se sobrepoem porque o flex encolhe todos abaixo do proprio texto

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

linha de arvore de requisitos e de execucoes desenha os rotulos uns por cima dos outros em 390px: id, cobertura, status e data se sobrepoem porque o flex encolhe todos abaixo do proprio texto

## What

`.repo-row` é um `flex` de uma linha só com os metadados soltos como irmãos:
prefixo da árvore, botão do título, selo de cobertura, selo de critérios,
selo de status, data e ações. Nenhum deles declara `flex-shrink`, então o
navegador encolhe **todos** proporcionalmente quando falta largura. Só o
título sabe encolher (tem `overflow: hidden` + reticências); os outros têm
`white-space: nowrap` e nenhum recorte, então o texto sai da caixa e é
DESENHADO POR CIMA do vizinho. Em 390 px a árvore de requisitos vira
`ST-0001`/`sem cobertura`/`active`/data empilhados no mesmo pixel, e a de
execuções fica pior ainda: `EXEC-0001` sob o nome do ciclo e o prazo
quebrado em seis linhas de duas letras.

O conserto tem duas partes, e as duas são necessárias:

1. **Quem não recorta, não encolhe.** Em `.repo-row`, só `.repo-file-main`
   (que tem `min-width: 0` e um filho com reticências) cede largura; selos,
   datas, prefixo e ações passam a `flex: 0 0 auto`. Isso acaba com a
   sobreposição em QUALQUER largura — inclusive num desktop com título
   longo, onde o mesmo defeito já existia calado.
2. **Em tela estreita a linha vira duas.** Com a sobreposição resolvida, os
   metadados ainda espremeriam o título até `Lo…`. Em `max-width: 860px` a
   linha ganha `flex-wrap` e os metadados descem para uma segunda linha,
   indentada sob o título — o identificador e o nome ficam inteiros na
   primeira.

**Afeta spec:** `design-system` — o critério 21 já governa a linha de tabela
densa; a linha de árvore não tinha regra equivalente.

## Scope boundaries

- Só a linha da árvore (`.repo-row` e filhos). Não mexe na tabela (`.row-actions`,
  `.overflow-menu`), que já foi tratada na change 0133.
- Não esconde informação: nada vira `wide-only` nesta change — o que não
  cabe na primeira linha desce para a segunda, e continua legível.
- Não toca no conteúdo semeado nem nas telas de detalhe.

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
- [x] Em 390 px, nenhuma caixa de texto da árvore de requisitos ou de
      execuções se sobrepõe à vizinha — medido no navegador comparando os
      retângulos de cada filho da linha, dois a dois.
- [x] Em 390 px o identificador (`ST-0001`, `EXEC-0001`) aparece inteiro,
      sem reticências, em toda linha da árvore.
- [x] Em 1440 px as mesmas árvores continuam numa linha só por item.

## Open questions

Nenhuma.
