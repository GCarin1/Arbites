# Spec Delta — capability: profile

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/profile/spec.md`

---

`GET /profile/avatar` responde hoje com `etag` e `last-modified`, e sem
`Cache-Control` nenhum. Duas consequências, e a segunda é a séria:

- **A foto trocada não aparece.** Sem diretiva explícita o navegador aplica
  cache heurístico e pode servir a imagem guardada sem revalidar. O
  contador de versão do cliente contorna isso enquanto a página está
  aberta, mas ele zera no recarregamento — e aí a URL volta a ser a mesma
  que o navegador já tem em cache. Trocar a foto e dar F5 mostra a antiga.
- **Imagem de conta em cache compartilhado.** O avatar é conteúdo por
  conta, servido atrás do mesmo gate de sessão de todo o resto. Sem
  `private`, um intermediário — e esta instância fica atrás de um túnel —
  está autorizado a guardar a resposta e entregá-la a outra pessoa.

A resposta certa é `Cache-Control: private, no-cache`: `private` proíbe o
cache compartilhado, e `no-cache` manda revalidar sempre, o que mantém o
ganho do `etag` (304 quando não mudou) sem o risco de servir imagem velha.

```ops
bump-version patch
append-requirement ubiquitous: The system shall servir o avatar da conta com `Cache-Control: private, no-cache`, para que o cache seja sempre revalidado e nenhum intermediário guarde imagem de uma conta.
append-criterion [unverified] O avatar responde com cache privado e revalidação obrigatória, e trocar a foto passa a servir a nova imagem com ETag diferente da anterior — verified by `backend/tests/test_avatar.py`.
```
