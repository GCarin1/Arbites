# Spec Delta — capability: auth

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/auth/spec.md`

---

```ops
append-requirement ubiquitous: The system shall oferecer um comando local que informe as contas existentes com papel e status, e que avise quando nao existe conta alguma, porque a recusa de login e indistinguivel de fora e de dentro da maquina a pessoa tem direito a resposta.
append-requirement ubiquitous: The system shall permitir criar ou redefinir localmente a conta de administrador, reativando-a e descartando o bloqueio por tentativas, sem nunca expor senha nem hash na saida.
append-criterion [unverified] Workspace sem conta explica o 401 e ensina o comando; criar e redefinir permitem entrar; conta pendente volta a ativa; senha curta e recusada sem tocar na conta; a listagem nunca mostra senha nem hash — verified by `backend/tests/test_recuperar_admin.py`.
bump-version minor
```
