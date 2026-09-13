# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

O quadro de execução é a tela onde o trabalho acontece, e é a única do
produto que **exige** um mouse. O card é uma `div` com `onClick`: não recebe
foco, não responde ao teclado, e mover um caso de coluna só existe como
arrastar. Quem navega por teclado consegue ler o quadro e não consegue
operá-lo.

Isso não é preferência de interação. Arrastar com precisão é justamente o
gesto que exclui quem tem limitação motora, e o Kanban não tem alternativa
nenhuma — nem menu de contexto, nem atalho. A tela vizinha, o modo guiado,
já resolve o mesmo problema por botões; o quadro ficou para trás.

Também falta o retorno: mover um card muda a tela em silêncio. Para quem usa
leitor de tela, o caso simplesmente some de um lugar sem nada ser dito.

```ops
bump-version minor
append-requirement ubiquitous: The system shall tornar cada card do quadro alcançável e operável por teclado — foco, abrir o resultado e mover entre colunas —, sem depender de arrastar.
append-requirement ubiquitous: The system shall identificar cada card e cada coluna do quadro para tecnologia assistiva, dizendo de que caso se trata e em que coluna ele está.
append-requirement event: When um caso muda de coluna, the system shall anunciar a mudança numa região viva, para que quem usa leitor de tela saiba o que aconteceu em vez de perceber o card sumir.
append-requirement unwanted: The system shall not oferecer no quadro nenhuma ação que exista apenas como arrastar; arrastar com precisão é o gesto que exclui quem tem limitação motora.
append-criterion [unverified] Um card do quadro recebe foco pelo teclado, abre o resultado por Enter e muda de coluna por atalho, com o mesmo efeito de arrastá-lo — verified by `frontend/src/components/Executions.tsx`.
append-criterion [unverified] Card e coluna se identificam para tecnologia assistiva e a mudança de coluna é anunciada numa região viva — verified by `frontend/src/components/Executions.tsx`.
```
