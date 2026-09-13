# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

```ops
append-requirement ubiquitous: The system shall montar todo estado vazio de lista de trabalho com marca visual, titulo da situacao, uma ou duas linhas dizendo o que mora ali, e a acao que resolve o vazio quando existe um proximo passo obvio, com a altura dada pelo conteudo.
append-requirement ubiquitous: The system shall distinguir a lista que nunca teve item da lista cujo filtro nao alcancou nenhum, oferecendo criar no primeiro caso e limpar o filtro no segundo, para que ninguem crie um item que ja existe escondido pelo recorte.
append-criterion [unverified] Num workspace novo as telas de test cases, requisitos, execucoes, defeitos e afazeres mostram estado vazio com marca, titulo, corpo e ao menos uma acao; com filtro que nao casa aparece o vazio de filtro, cuja acao e limpar — verified by `frontend/src/components/EmptyState.tsx` + `frontend/src/styles.css`.
bump-version minor
```
