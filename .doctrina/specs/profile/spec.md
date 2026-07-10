# Spec — profile

**Capability:** profile
**Status:** active
**Implementation:** verified — M13 (backend/arbites/api.py; frontend Profile.tsx). Memória injetada nos 5 usos de IA
**Realizes:** SC14
**Last updated:** 2026-07-09
**Version:** 0.1.0

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

### State-driven

- While a memória está vazia, the system shall chamar a IA sem bloco de
  contexto (sem ruído no prompt).

### Unwanted-behavior (must-not)

- The system shall not enviar a memória para qualquer lugar além do provider
  de IA explicitamente configurado (local-first; sem telemetria).

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

## Maturity

**MVP (committed):**

- profile.md, GET/PUT, template com 2 seções, injeção em todas as funções
  de IA, aba Perfil na UI.

**Future (aspirational, not committed):**

- IA propõe atualizações da memória (com aceite); múltiplos perfis.

## Out of scope for this spec

- Autenticação/multiusuário (single-user local).
