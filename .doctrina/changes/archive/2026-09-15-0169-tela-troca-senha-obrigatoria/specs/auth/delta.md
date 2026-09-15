# Spec Delta — capability: auth

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/auth/spec.md`

---

A obrigação de trocar a senha existia no backend e nunca chegava à tela: o
`<Login>` era reaproveitado entre as duas fases do porteiro e mantinha o modo
antigo, e a fase de troca dava a sessão por concluída sem conferir se a
obrigação tinha saído. O requisito passa a cobrir a saída, não só a recusa.

```ops
append-requirement event: When o login devolve uma conta que ainda deve a troca de senha, the system shall apresentar a tela de troca em vez da tela de entrada, e só considerar a sessão concluída quando a obrigação sair — jamais por ter havido um login bem-sucedido.
append-requirement state: While a sessão está presa na troca obrigatória com o app já montado, the system shall devolver a SPA à tela de troca ao receber `password_change_required`, em vez de manter as telas pedindo dados que nunca chegam.
append-requirement ubiquitous: The system shall oferecer a troca da própria senha a qualquer momento pela tela de perfil, sem depender de obrigação pendente nem de intervenção de um admin.
append-criterion [verified] O login de uma conta que deve a troca abre a tela de troca (não a de entrada), a recusa das demais rotas traz o código `password_change_required`, as três rotas de saída continuam abertas, e trocar a senha libera o app na mesma sessão — verified by `backend/tests/test_troca_obrigatoria.py`.
set-header Last updated: 2026-09-15
bump-version patch
```
