# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

O menu lateral é a primeira coisa que se vê e hoje parece uma lista de rotas,
não a navegação de um produto. Quatro problemas concretos:

**Mais cabeçalho do que conteúdo.** Cinco títulos de grupo para doze itens
visíveis. "Ferramentas" tem **um** item — um cabeçalho para um item é ruído
puro, ocupa uma linha inteira para dizer o que o próprio item já diz.

**Nenhum ícone.** Só texto alinhado à esquerda. É o que separa um menu que
se lê varrendo de um menu que se lê palavra por palavra: o ícone dá âncora
visual e permite achar "Execuções" sem ler os outros onze.

**Navegação duplicada.** "Perfil" e "Administração" estão no menu lateral e
no menu do avatar, que existe desde a change 0110 justamente para responder
"com que conta estou". Perfil é da pessoa e pertence ao avatar; o menu
lateral é do workspace.

**Nada ancorado embaixo.** "Suporte" — Problemas, Perfil, Administração —
flutua no meio do fluxo, entre o trabalho e o que foi congelado. Numa
ferramenta profissional o que é de manutenção fica no rodapé da navegação,
separado por uma régua, porque não compete com o trabalho do dia.

A reorganização não tira nenhuma tela do alcance: Perfil continua a um clique
no avatar e o endereço direto dele continua funcionando.

```ops
bump-version minor
append-requirement ubiquitous: The system shall acompanhar cada item do menu lateral de um ícone, para que a navegação seja varrida e não lida item a item.
append-requirement ubiquitous: The system shall agrupar o menu lateral apenas onde o grupo esclarece — sem cabeçalho para grupo de um item só — e ancorar no rodapé, separado por régua, o que é de manutenção e não de trabalho do dia.
append-requirement unwanted: The system shall not repetir no menu lateral a navegação que o menu da conta já oferece; o perfil é da pessoa e pertence ao avatar, o menu lateral é do workspace.
append-criterion [unverified] O menu lateral tem ícone em todo item, nenhum cabeçalho de grupo com um item só, e o que é de manutenção ancorado no rodapé depois de uma régua — verified by `frontend/src/App.tsx` + `frontend/src/styles.css`.
append-criterion [unverified] Nenhuma tela sai do alcance na reorganização: o que deixa o menu lateral continua acessível pelo menu da conta e pelo endereço direto — verified by `frontend/src/App.tsx`.
```
