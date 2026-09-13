# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

Quando a requisição não chega a ter resposta — servidor fora do ar,
container reiniciando, aparelho em outra rede —, o `fetch` do navegador
rejeita com a própria mensagem interna dele. Ninguém a intercepta, e ela vai
crua para a tela: **"Failed to fetch"**, em inglês, num produto em
português, dentro da caixa vermelha de erro do login.

Para quem está olhando, isso é indistinguível de "a senha está errada". A
pessoa tenta de novo, troca a senha, desconfia da conta — quando o problema
não está nela nem na credencial: o servidor não respondeu.

São dois estados diferentes e o produto precisa dizer qual é:

- **O servidor respondeu e recusou** — credencial inválida, permissão,
  validação. A mensagem vem do servidor e já está certa.
- **O servidor não respondeu** — e aí a mensagem tem de dizer isso, em
  português, e apontar o que verificar.

```ops
bump-version patch
append-requirement event: When uma requisição falha antes de obter resposta do servidor, the system shall informar que não foi possível falar com o servidor, em português e indicando o que verificar, em vez de repassar a mensagem interna do navegador.
append-criterion [unverified] Uma falha de rede produz mensagem em português distinguindo "o servidor não respondeu" de uma recusa do servidor, em toda chamada — inclusive nos envios de arquivo — verified by `frontend/src/api.ts`.
```
