---
name: fonte-do-preview-diverge-da-fonte-da-operacao
description: Quando um fluxo tem preview (antes de salvar) e operação (depois de salvar) mostrando "a mesma" lista, as duas devem ler da MESMA fonte — um filtro implícito só na segunda (ex.: exigir tag/vínculo) faz o preview prometer o que a operação não entrega, e o usuário vê sucesso seguido de vazio inexplicável.
when: O agente está implementando ou depurando um fluxo em duas etapas (preview/validação → salvar → usar) onde a mesma informação aparece antes e depois de persistir, vinda de caminhos de código diferentes.
---

# Skill — fonte-do-preview-diverge-da-fonte-da-operacao

## When to use this skill

- O agente cria um formulário com botão "testar/procurar/validar" que lista
  resultados ANTES de salvar, e uma tela de operação que lista "os mesmos"
  resultados DEPOIS (dropdown, select, tabela).
- O agente depura um sintoma do tipo "no preview aparece, depois de salvar
  some" ou "validou ok mas a operação recusa (4xx)".

## Procedure

1. **Mapeie as duas fontes.** Encontre de onde o preview lê (geralmente um
   scan direto/avulso) e de onde a operação lê (geralmente o índice/tabela
   persistida). Se são caminhos de código diferentes, pergunte: o segundo
   caminho tem algum FILTRO que o primeiro não tem (tag obrigatória,
   vínculo, status, prefixo)?
2. **Prefira uma fonte só.** Se a operação pode ler da mesma fonte do
   preview (ex.: re-listar do disco com o config salvo), unifique. A
   informação derivada (o que está mapeado/vinculado) entra como ANOTAÇÃO
   sobre a lista, não como filtro que esvazia a lista.
3. **Se o filtro é inevitável, ele precisa falar.** Uma lista vazia após um
   preview cheio DEVE explicar o porquê na UI ("N itens encontrados, 0
   atendem ao critério X — faça Y") — nunca um select vazio mudo seguido de
   um 4xx genérico na ação.
4. **Teste com o dado "de fora".** O fixture do teste deve representar o
   mundo sem as convenções do produto (repositório sem as tags/estrutura
   esperadas) — é exatamente o dado que um usuário novo traz no primeiro
   uso.

## Anti-patterns

- Browse de `.feature` lista os arquivos do disco (glob puro), mas o
  dropdown pós-save lê da tabela `scenarios` que só contém cenários
  tagueados `@CT-` — repositório real sem tags Arbites: preview cheio,
  dropdown vazio, run `422 empty_selection` (bug real, change 0067).
- Culpar o dado do usuário (encoding do caminho, acentos, pasta
  sincronizada na nuvem) antes
  de comparar as duas fontes — se o preview funcionou com o mesmo input, o
  input não é a causa.
- "Consertar" exibindo a lista do preview mas mantendo a operação lendo da
  fonte filtrada — o vazio só muda de lugar (o select enche, o run continua
  recusando).

## Related material

- `.doctrina/changes/0067-fix-automacao-target-salvo-com-feature/` — o caso
  completo (diagnóstico + correções propostas).
- `backend/arbites/gherkin_scan.py` — `list_feature_files` (fonte do
  preview) vs `scan_target` (fonte filtrada da operação).
- [[lista-vazia-nao-e-sem-filtro]] — prima: estados de filtro que colapsam.
- [[novo-consumidor-repassa-config-do-helper]] — o bug irmão do prefixo
  hardcoded (`_CT_TAG_RE`).
