# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

A barra superior está em todas as telas o tempo todo, e carrega duas coisas
que não deveriam estar ali.

**O caminho do diretório no disco** — `/tmp/arb-demo/w` — ocupa espaço fixo
no topo de toda tela. É informação de instalação, consultada uma vez por
mês por quem edita no Obsidian, e está com o mesmo peso permanente da busca.
Nenhuma ferramenta profissional expõe o caminho do disco na barra superior.

**"Reindexar" como botão de destaque.** É manutenção — reconstruir o índice
descartável (ADR 0001) — e está com a mesma aparência de uma ação de
trabalho, ao lado do avatar, disputando atenção com a busca em toda tela.

E, na tela de Execuções, o botão do modo guiado ficou **acima** do título
da página, solto, antes do H1. Um controle antes do título da página não
pertence a lugar nenhum: ele não é navegação nem é ação da página.

Nada disso some do produto: o caminho fica a um passar de mouse sobre o
nome do workspace, e reindexar continua a um clique.

```ops
bump-version patch
append-requirement ubiquitous: The system shall reservar a barra superior para identidade, busca e conta, mantendo informação de instalação e ação de manutenção acessíveis sem ocupar espaço permanente nela.
append-requirement ubiquitous: The system shall posicionar as ações de uma tela dentro do cabeçalho dela, nunca antes do título da página.
append-criterion [unverified] A barra superior não exibe caminho de disco nem ação de manutenção como botão de destaque, e ambos continuam alcançáveis — verified by `frontend/src/App.tsx`.
append-criterion [unverified] Nenhuma tela tem controle renderizado antes do título da página — verified by `frontend/src/App.tsx`.
```
