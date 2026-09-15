# Spec Delta — capability: auth

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/auth/spec.md`

---

Cadastro pendente numa instância sem admin ativo é um beco sem saída: não
existe quem aprove, e nada na tela diz isso. A instância passa a revelar o
estado e a deixar o e-mail declarado no ambiente tomar posse uma única vez
(ADR 0018).

```ops
replace-requirement event 1: When um cadastro é submetido, the system shall criar a conta com status `pending` e papel `viewer`, sem abrir sessão — exceto quando não existe nenhum admin ativo e o e-mail informado é exatamente `ARBITES_ADMIN_EMAIL`, caso em que a conta nasce `admin` e `active` com a senha escolhida no próprio cadastro.
append-requirement state: While não existe nenhum admin ativo, the system shall informar esse estado em `GET /auth/me` a quem ainda não tem sessão, junto com a indicação de haver ou não `ARBITES_ADMIN_EMAIL` declarado, para que a tela diga qual das duas saídas serve antes de alguém se cadastrar em vão.
append-requirement unwanted: The system shall not deixar o e-mail de `ARBITES_ADMIN_EMAIL` nascer `admin` enquanto existir ao menos um admin ativo; a posse da instância órfã acontece uma vez, não é uma porta permanente.
append-criterion [verified] Sem admin ativo, `GET /auth/me` responde `no_admin` e a tela avisa antes do cadastro; o e-mail de `ARBITES_ADMIN_EMAIL` nasce admin ativo sem troca de senha obrigatória e entra no login seguinte, e qualquer outro e-mail continua pendente; com um admin ativo o mesmo e-mail volta a nascer pendente — verified by `backend/tests/test_primeiro_dono.py`.
set-header Implementation: verified — `backend/arbites/auth.py`, `backend/arbites/api.py` (rotas /auth/* + gate), `frontend/src/components/AuthGate.tsx`
set-header Last updated: 2026-09-14
bump-version minor
```
