---
name: criterio-de-isolamento-precisa-de-identidade-colidente
description: Critério que prova isolamento entre contas com dois valores obviamente diferentes não prova nada — ele tem de usar duas identidades que COLIDEM na função que deriva a chave (slug, hash curto, normalização).
when: Ao escrever ou revisar critério de aceite de isolamento por conta/tenant; ao derivar caminho de arquivo, chave de cache ou id a partir de e-mail, nome ou título; ao ver "shall not expor X de uma conta a outra" num spec.
---

# Skill — criterio-de-isolamento-precisa-de-identidade-colidente

## When to use this skill

- Um spec diz "não expor o dado de uma conta a outra" e você vai escrever o
  critério que prova isso.
- Você vai derivar um caminho de arquivo, uma chave ou um id a partir de um
  texto do usuário (e-mail, nome, título) com `slugify`, `normalize`, hash
  curto ou `lower()`.
- Revisão de critério já marcado `[verified]` numa capability multiusuário.

## O bug (real, change 0119)

O spec `profile` tinha, verificado há duas changes:

> The system shall not injetar em uma chamada de IA a memória de outra conta,
> nem expor o perfil de uma conta a outra por nenhuma rota.

O critério que o provava usava `admin@arbites.test` e `outra@arbites.test` —
duas contas, dois arquivos, tudo separado, verde. Mas o caminho vinha de
`profiles/<slugify(email)>.md`, e `slugify` colapsa **qualquer** sequência
não alfanumérica num único hífen:

```
ana.silva@arbites.test  ->  ana-silva-arbites-test
ana-silva@arbites.test  ->  ana-silva-arbites-test   # mesmo arquivo
```

Duas contas reais, um arquivo só: a segunda lia o nome e a memória de longo
prazo da primeira — a mesma memória injetada em toda chamada de IA —,
recebia o avatar dela e sobrescrevia o perfil sem aviso. O critério estava
verde porque testava o caminho feliz da identidade.

## Procedure

1. **Ache a função que deriva a chave** (`slugify`, hash truncado,
   normalização de acento, `casefold`). Leia a implementação, não o nome.
2. **Construa o par colidente**: dois valores de entrada distintos que a
   função mapeia para a MESMA saída. Para `slugify`, troque um separador por
   outro (`.` ↔ `-` ↔ `_` ↔ `+`). Para hash truncado, o par vem de busca —
   se não achar, documente o tamanho e a colisão esperada.
3. **Fixe a premissa no próprio teste**, para a prova não esvaziar em
   silêncio se a função mudar:
   ```python
   def test_os_dois_emails_realmente_colidem_no_slug():
       assert slugify(ANA["email"]) == slugify(OUTRO["email"])
   ```
4. **Prove as três direções**: A não lê o de B; B não sobrescreve o de A;
   e cada um tem seu próprio arquivo/linha no armazenamento.
5. **Se corrigir a derivação**, acrescente adoção do nome antigo — sem ela a
   correção não perde o dado, mas o torna inalcançável, que dá na mesma para
   quem escreveu.

## Anti-patterns

- Critério de isolamento com `user1@x.com` / `user2@x.com`: distingue por
  qualquer derivação, inclusive uma quebrada.
- Confiar no nome da função (`slugify` "parece" seguro para identidade — ele
  é seguro para NOMEAR artefatos, onde o ID no frontmatter identifica; ADR
  0002).
- Trocar a chave legível por um id numérico "para garantir": num produto em
  que o filesystem é a fonte de verdade (ADR 0001), `7.md` não diz de quem é
  o arquivo. Slug legível + sufixo unívoco resolve os dois lados.

## Related material

- `.doctrina/changes/archive/2026-09-13-0119-e-mails-diferentes-colidem-mesmo/`
- `backend/tests/test_profile_identity.py` — o par colidente e as três direções.
- `backend/arbites/api.py` — `_account_slug()`, `_adopt_legacy_name()`.
