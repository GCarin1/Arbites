# Spec Delta — capability: profile

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/profile/spec.md`

---

O perfil de uma conta mora em `profiles/<slug-do-e-mail>.md` e o avatar em
`profiles/avatars/<slug-do-e-mail>.<ext>`. O `slugify()` troca **qualquer**
sequência de caracteres não alfanuméricos por um único hífen — então
`ana.silva@arbites.test` e `ana-silva@arbites.test` produzem o mesmo slug.

Duas contas distintas, um arquivo só. O efeito, reproduzido:

- A segunda conta lê o nome e a **memória de longo prazo** da primeira — a
  mesma memória que é injetada em toda chamada de IA. A função que resolve o
  caminho já dizia, no próprio comentário, que compartilhar o arquivo "faria
  a IA responder a um QA com o contexto de outro".
- A segunda conta recebe o **avatar** da primeira.
- Quem gravar por último sobrescreve o perfil do outro, sem aviso.

Isso contradiz um requisito que o spec já tem e dá como verificado: não
expor o perfil de uma conta a outra por nenhuma rota. O critério que o
provava testava duas contas com e-mails que não colidem — a colisão passou
por baixo dele.

A correção é a identidade do arquivo: o slug continua na frente, porque um
workspace aberto no Obsidian precisa dizer de quem é cada arquivo, e ganha
atrás um sufixo curto derivado do e-mail inteiro. Legível e único.

```ops
bump-version minor
append-requirement ubiquitous: The system shall derivar o nome do arquivo de perfil e de avatar de uma conta de forma unívoca — slug legível mais um sufixo curto derivado do e-mail completo —, para que duas contas nunca resolvam o mesmo caminho.
append-requirement event: When a conta tem perfil ou avatar gravado sob o nome antigo, apenas baseado no slug, the system shall adotá-lo no nome novo na primeira leitura, para não perder a memória já escrita.
append-requirement unwanted: The system shall not usar o slug do e-mail sozinho como identidade de arquivo por conta; `slugify` colapsa pontuações diferentes no mesmo texto e duas contas distintas passariam a compartilhar o arquivo.
append-criterion [unverified] Duas contas cujos e-mails colidem no slug têm perfis, memórias e avatares separados, e nenhuma das duas lê ou sobrescreve o da outra — verified by `backend/tests/test_profile_identity.py`.
append-criterion [unverified] Um perfil e um avatar gravados sob o nome antigo continuam sendo os da conta depois da atualização, sem perda da memória escrita — verified by `backend/tests/test_profile_identity.py`.
```
