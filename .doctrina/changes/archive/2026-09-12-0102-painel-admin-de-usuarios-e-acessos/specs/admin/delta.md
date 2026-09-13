# Spec Delta — capability: admin

**Operation:** ADDED
**Target spec on apply:** `.doctrina/specs/admin/spec.md`

---

# Spec — admin

**Capability:** admin
**Status:** active
**Implementation:** verified — `backend/arbites/api.py` (rotas /admin/*), `frontend/src/components/Admin.tsx`
**Realizes:** SC16
**Last updated:** 2026-09-12
**Version:** 0.1.0

## Purpose

A superfície de governo da instância compartilhada: quem entra, quem já
entrou e o que está ligado. O `auth` decide se uma requisição passa; o
`admin` é onde uma pessoa olha para essas decisões e as altera — libera um
cadastro, derruba uma sessão, rebaixa um papel, desliga o runner.

O princípio que organiza a capability: **o painel governa acesso, não
conteúdo.** Um admin não edita o CT de outra pessoa por aqui; ele decide
quem pode editar. Isso mantém a cadeia de rastreabilidade honesta — o autor
de um artefato é sempre quem o escreveu.

O segundo princípio: **conta não se apaga.** Desativar preserva a autoria
histórica das execuções; apagar reescreveria o passado.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /admin/users` (apenas `admin`) com, por conta,
  e-mail, nome, papel, status, data de criação, último login e número de
  sessões abertas.
- The system shall expor as ações de governo, todas restritas a `admin`:
  `POST /admin/users/{id}/approve`, `.../reject`, `.../disable`,
  `.../enable`, `PUT /admin/users/{id}/role`,
  `POST /admin/users/{id}/password` (define uma senha temporária com troca
  obrigatória) e `DELETE /admin/users/{id}/sessions` (encerra as sessões).
- The system shall expor `GET /admin/access-log` (apenas `admin`) com as
  tentativas de autenticação — e-mail informado, sucesso ou falha, IP,
  user-agent e data — mais recente primeiro, paginado por `limit` e
  `offset`.
- The system shall expor `GET /admin/overview` (apenas `admin`) com o
  retrato operacional que a aba Sistema mostra: contagem de contas por
  status, estado do índice, tamanho da lixeira e versão.
- The system shall oferecer no frontend uma seção Administração visível
  somente ao papel `admin`, com as abas Usuários, Acessos e Sistema.
- The system shall destacar a fila de cadastros pendentes na aba Usuários,
  porque é o único item da tela que bloqueia outra pessoa de trabalhar.

### Event-driven

- When um admin aprova um cadastro pendente, the system shall ativá-lo com o
  papel escolhido no momento da aprovação (default `viewer`), sem exigir uma
  segunda ação para definir o papel.
- When um admin define uma senha temporária para outra conta, the system
  shall marcá-la com troca obrigatória e encerrar as sessões dela.
- When um admin altera o próprio papel ou o próprio status, the system shall
  recusar a operação com código `self_demotion` — a saída de um admin é
  decisão de outro admin.

### State-driven

- While não há nenhum cadastro pendente, the system shall dizê-lo
  explicitamente na aba Usuários em vez de mostrar uma lista vazia sem
  contexto.
- While uma conta tem sessões abertas, the system shall permitir encerrá-las
  sem alterar o status da conta — derrubar quem está dentro e barrar quem
  quer entrar são decisões separadas.

### Unwanted-behavior (must-not)

- The system shall not oferecer exclusão de conta; desativar preserva a
  autoria histórica das execuções e defeitos, apagar reescreveria o passado.
- The system shall not permitir, por nenhuma rota deste painel, que o último
  admin ativo seja desativado, recusado ou rebaixado.
- The system shall not expor hash de senha nem identificador de sessão em
  nenhuma resposta, nem mesmo ao `admin`.
- The system shall not permitir edição de artefato de QA a partir do painel;
  ele governa acesso, não conteúdo.

### Optional

- Where o operador quiser auditar fora da UI, the system may permitir
  filtrar o log de acesso por e-mail e por resultado.

## Acceptance criteria

1. [verified] Um cadastro aparece na fila de pendentes e, aprovado com
   papel `editor`, a conta passa a logar já como `editor` numa só ação —
   verified by `backend/tests/test_admin_panel.py`.
2. [verified] Desativar uma conta encerra as sessões dela e a lista passa
   a mostrar zero sessões abertas; reativar não devolve a sessão antiga —
   verified by `backend/tests/test_admin_panel.py`.
3. [verified] Definir uma senha temporária derruba as sessões, obriga a
   troca no login seguinte e não vaza o hash em nenhuma resposta — verified
   by `backend/tests/test_admin_panel.py`.
4. [verified] O log de acesso lista sucesso e falha com IP e data, mais
   recente primeiro, e pagina por `limit`/`offset` — verified by
   `backend/tests/test_admin_panel.py`.
5. [verified] Nenhuma rota do painel responde a papel diferente de
   `admin`, e nenhuma delas apaga conta — verified by
   `backend/tests/test_admin_panel.py`.
6. [verified] Um admin não consegue rebaixar nem desativar a si mesmo, e o
   último admin ativo é intocável por qualquer rota do painel — verified by
   `backend/tests/test_admin_panel.py`.
7. [verified] `GET /admin/overview` responde contagem por status, estado
   do índice, tamanho da lixeira e versão — verified by
   `backend/tests/test_admin_panel.py`.

## Maturity

**MVP (committed):**

- Usuários (aprovar, recusar, ativar, desativar, papel, senha temporária,
  encerrar sessões), Acessos (log de autenticação) e Sistema (interruptores,
  índice, lixeira, versão).

**Future (aspirational, not committed):**

- Convite por link com expiração, em vez de cadastro aberto.
- Exportação do log de acesso em CSV.
- Grupos de usuários com papel herdado.

## Out of scope for this spec

- Autenticação, sessão e lockout (ver `auth`).
- Alcance de cada papel e os interruptores em si (ver `auth`); aqui eles são
  apenas exibidos e alternados.
- Log de escrita de artefatos (ver `audit`).
