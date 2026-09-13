# Spec — profile

**Capability:** profile
**Status:** active
**Implementation:** verified — perfil por conta, autoria pela sessão e avatar da conta (`backend/arbites/api.py`, `frontend/src/components/Profile.tsx`, `frontend/src/components/AccountMenu.tsx`, `frontend/src/components/Identicon.tsx`, `frontend/src/api.ts`)
**Realizes:** SC14
**Last updated:** 2026-09-13
**Version:** 0.3.1

## Purpose

Seção de Perfil com as informações do usuário e a **memória de longo prazo
para IA**: um Markdown editável na interface com duas seções — *Preferências
& Estilo* (como o usuário quer que a IA interaja) e *Contexto Ativo*
(projetos/decisões em andamento). Esse conteúdo é injetado como contexto em
**toda** interação com IA da ferramenta, independente do provider (M5). A
fonte de verdade é `profile.md` na raiz do workspace (ADR 0001).

## Requirements (EARS)

### Ubiquitous

- The system shall persistir o perfil em `profile.md` (frontmatter `name`;
  corpo = memória com as seções "Preferências & Estilo" e "Contexto Ativo").
- The system shall expor `GET/PUT /profile` (nome + memória), criando o
  arquivo com template na primeira leitura.
- The system shall injetar a memória como contexto de usuário em toda
  chamada de IA (geração/revisão/negativos/daily/resumo de reunião),
  independente do provider configurado.
- The system shall persistir o perfil de cada conta em `profiles/<slug-do-e-mail>.md`, com a mesma estrutura de antes (frontmatter `name`; corpo com "Preferências & Estilo" e "Contexto Ativo").
- The system shall preencher a autoria a partir da sessão, e não do corpo da requisição: `owner` de uma execution e `created_by` no frontmatter de requisito, caso de teste e defeito recebem o e-mail de quem está logado.
- The system shall expor `GET /profile/avatar` e `PUT /profile/avatar` para a conta da sessão, aceitando PNG, JPEG ou WebP de até 1 MB, e `DELETE /profile/avatar` para voltar ao identicon.
- The system shall guardar o avatar em `profiles/avatars/<slug-do-e-mail>.<ext>`, ao lado do perfil da conta, sem passar pelo índice descartável.
- The system shall exibir o avatar da conta logada no canto superior direito de toda tela, abrindo um menu com Perfil, Administração (apenas para `admin`) e Sair.
- The system shall servir o avatar da conta com `Cache-Control: private, no-cache`, para que o cache seja sempre revalidado e nenhum intermediário guarde imagem de uma conta.

### Event-driven

- When um artefato é criado, the system shall gravar `created_by` no frontmatter dele; edições posteriores preservam o valor original, porque quem criou não muda.
- When uma conta lê o próprio perfil pela primeira vez e ainda não existe arquivo para ela, the system shall criá-lo a partir do template — exceto para a conta de menor id, que herda o `profile.md` da raiz uma única vez, preservando a memória escrita antes da instância virar multiusuário.
- When a conta não tem imagem, the system shall desenhar um identicon determinístico — grade 5×5 espelhada e cor derivadas do hash do e-mail — gerado no cliente, sem requisição a serviço externo.

### State-driven

- While a memória está vazia, the system shall chamar a IA sem bloco de
  contexto (sem ruído no prompt).
- While a instância roda sem autenticação (`ARBITES_AUTH=off`), the system shall continuar usando o `profile.md` da raiz e gravar autoria como `local`, para que a instalação de uma pessoa só não mude de comportamento.

### Unwanted-behavior (must-not)

- The system shall not enviar a memória para qualquer lugar além do provider
  de IA explicitamente configurado (local-first; sem telemetria).
- The system shall not injetar em uma chamada de IA a memória de outra conta, nem expor o perfil de uma conta a outra por nenhuma rota.
- The system shall not aceitar autoria vinda do corpo da requisição; um cliente que envie `owner` tem o valor ignorado, senão a autoria vira um campo que qualquer um preenche com o nome de qualquer um.
- The system shall not buscar avatar em serviço externo (Gravatar ou equivalente); enviar o hash do e-mail de cada conta para fora contraria o local-first e a promessa de zero telemetria.
- The system shall not aceitar como avatar arquivo que não seja imagem reconhecida por assinatura de bytes, nem confiar na extensão informada pelo cliente.

### Optional

- Where o usuário pedir, the system may permitir que a própria IA proponha
  atualizações da memória (Future — hoje a edição é manual na UI).

## Acceptance criteria

1. [verified] `GET /profile` cria/retorna template com as duas seções;
   `PUT` persiste nome e memória em `profile.md` — verified by
   `backend/tests/test_profile.py`.
2. [verified] A memória é injetada no prompt de toda chamada de IA
   (verificado capturando o payload enviado ao provider mock) — verified by
   `backend/tests/test_profile.py`.
3. [verified] Memória vazia → prompt sem bloco de contexto — verified by
   `backend/tests/test_profile.py`.
4. [verified] Duas contas editam o próprio perfil e cada uma lê apenas o seu; a memória injetada no prompt de IA é a de quem chamou — verified by `backend/tests/test_authorship.py`.
5. [verified] Uma execution criada por uma conta nasce com `owner` igual ao e-mail dela, mesmo que o corpo da requisição peça outro — verified by `backend/tests/test_authorship.py`.
6. [verified] Requisito, caso de teste e defeito nascem com `created_by` no frontmatter, e editar o artefato depois não troca esse valor — verified by `backend/tests/test_authorship.py`.
7. [verified] A conta de menor id herda o `profile.md` da raiz uma vez; a segunda conta começa do template sem enxergar a memória da primeira — verified by `backend/tests/test_authorship.py`.
8. [verified] Com `ARBITES_AUTH=off` o perfil continua sendo o `profile.md` da raiz e a autoria gravada é `local` — verified by `backend/tests/test_authorship.py`.
9. [verified] Uma conta sobe uma imagem, ela aparece no canto superior direito e sobrevive ao reinício do processo; removê-la volta ao identicon — verified by `backend/tests/test_avatar.py`.
10. [verified] Duas contas sem foto recebem identicons diferentes, e a mesma conta recebe sempre o mesmo desenho — verified by `frontend/src/components/Identicon.tsx` + `backend/tests/test_avatar.py`.
11. [verified] O avatar de uma conta não é legível por outra, e um arquivo que não é imagem é recusado mesmo com extensão de imagem — verified by `backend/tests/test_avatar.py`.
12. [verified] O avatar responde com cache privado e revalidação obrigatória, e trocar a foto passa a servir a nova imagem com ETag diferente da anterior — verified by `backend/tests/test_avatar.py`.

## Maturity

**MVP (committed):**

- profile.md, GET/PUT, template com 2 seções, injeção em todas as funções
  de IA, aba Perfil na UI.

**Future (aspirational, not committed):**

- IA propõe atualizações da memória (com aceite); múltiplos perfis.

## Out of scope for this spec

- Autenticação/multiusuário (single-user local).
