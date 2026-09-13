# Change 0110-navegacao-e-identidade-no-padrao-github — Navegacao e identidade no padrao GitHub

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (confident; signals: para que)
- **Affects specs:** profile

## Why

Barra superior fina com busca, criacao rapida e o avatar da conta a direita, abrindo o menu de Perfil, Administracao e Sair. Avatar com identicon de cubos gerado do e-mail como padrao e upload de imagem opcional, sem chamar servico externo. Navegacao lateral reagrupada, com o que foi congelado atras de um menu Mais, para que as dezoito abas de hoje deixem de competir com o nucleo.

## What

- `profile` (spec MODIFIED): o avatar da conta vira parte da identidade —
  `GET/PUT/DELETE /profile/avatar` guardando a imagem em
  `profiles/avatars/<slug-do-e-mail>.<ext>`, com o formato decidido por
  assinatura de bytes, e o identicon determinístico desenhado no cliente
  quando não há foto.
- `backend/arbites/api.py`: as três rotas, o sniff de imagem (PNG, JPEG,
  WebP) e o teto de 1 MB.
- `backend/tests/test_avatar.py`: a prova dos três critérios novos.
- `frontend/src/components/Identicon.tsx`: grade 5×5 espelhada, hash FNV-1a
  do e-mail, SVG gerado no cliente.
- `frontend/src/components/AccountMenu.tsx`: avatar no canto superior
  direito com o menu Perfil · Administração (só `admin`) · Sair.
- `frontend/src/components/Profile.tsx`: trocar a foto e voltar ao
  identicon.
- A navegação lateral reagrupada com o grupo "Mais" já tinha entrado com o
  ADR 0012; esta mudança fecha a parte de identidade.

## Scope boundaries

- Não mexe em autenticação, papéis ou aprovação de contas (capability
  `auth`): o avatar é exibição de identidade, não controle de acesso.
- Não redimensiona nem reencoda a imagem enviada — o teto de 1 MB resolve
  o custo sem trazer uma dependência de processamento de imagem.
- Não troca o avatar de terceiros: cada conta só lê e escreve o seu.
- Não toca nas capabilities congeladas pelo ADR 0012.
- `App.tsx` (capability `home`) e `styles.css` (capability `design-system`)
  são tocados, mas os specs delas ficam como estão: o requisito do avatar no
  canto superior direito é da capability `profile`, e o CSS novo apenas
  consome os tokens já fixados pelo design-system, sem criar componente
  canônico nem mudar a aparência de nenhum dos existentes.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

Nenhuma.
