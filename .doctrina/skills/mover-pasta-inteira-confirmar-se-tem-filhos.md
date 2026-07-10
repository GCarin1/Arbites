---
name: mover-pasta-inteira-confirmar-se-tem-filhos
description: Ao permitir arrastar/mover uma pasta inteira (não só um item) numa árvore, distinga o tipo do item arrastado (item vs container), bloqueie soltar um container nele mesmo/numa descendente, e confirme antes de mover se o container tiver filhos que "vão junto" sem o usuário ter escolhido cada um.
when: Ao implementar drag & drop de pastas/containers hierárquicos (não só itens-folha) numa árvore com backend que espelha o filesystem.
---

# Skill — mover-pasta-inteira-confirmar-se-tem-filhos

## When to use this skill

- Uma árvore de pastas já suporta arrastar ITENS-FOLHA entre pastas (CT,
  arquivo) e o pedido é estender para arrastar a PRÓPRIA PASTA.

## Procedure

1. **Distinga o tipo do que está sendo arrastado.** Um estado único
   `dragId: string` (só id de item-folha) não escala — use uma união
   discriminada (`{kind:"item", id} | {kind:"folder", path, childCount}`) e
   ramifique a lógica de drop por `kind`.
2. **Bloqueie ciclos no client E no backend.** Soltar uma pasta nela mesma ou
   numa descendente (`destPath === srcPath || destPath.startsWith(srcPath+"/")`)
   deve ser rejeitado nos dois lados — no client evita UX confusa (não
   preveni `dragover` ali, então o browser nem mostra o cursor de "pode
   soltar"); no backend é a garantia real (422).
3. **Conte os filhos ANTES de perguntar.** Ao iniciar o drag, calcule
   `childCount` (recursivo) da pasta. Se `childCount > 0`, a pasta "carrega"
   itens que o usuário não selecionou individualmente — abra um
   `ConfirmModal` citando a contagem ("contém N casos de teste, que serão
   movidos junto") ANTES de chamar a API. Se `childCount === 0`, mova direto
   (perguntar por uma pasta vazia é atrito sem valor).
4. **Backend: mova a subárvore inteira, não arquivo por arquivo.**
   `Path.rename(diretório)` é atômico e move tudo de uma vez; colete os
   caminhos afetados (`rglob("*.md")`) ANTES do rename para saber o que
   reindexar como "removido do caminho antigo", depois reindexe os caminhos
   NOVOS (`rglob` de novo, pós-rename).
5. **Reuse o guard de destino já existente** (`_safe_area_dir`/traversal) em
   vez de duplicar a validação de path para a nova rota.

## Anti-patterns

- Deixar `dragId` tipado só para item-folha e "gambiarrar" pasta por cima.
- Perguntar confirmação sempre, mesmo para pasta vazia (atrito sem sinal).
- Mover arquivo por arquivo numa pasta em vez de `rename()` do diretório.

## Related material

- `backend/arbites/api.py` — `move_tc_folder`, `_safe_area_dir`.
- `frontend/src/components/TcRepository.tsx` — `DragState`, `isDescendantOrSelf`,
  `pendingFolderMove`.
- `backend/tests/test_tc_repository.py`.
