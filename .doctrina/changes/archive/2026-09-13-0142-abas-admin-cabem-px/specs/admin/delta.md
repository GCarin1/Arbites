# Spec Delta — capability: admin

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/admin/spec.md`

---

```ops
append-requirement ubiquitous: The system shall manter toda acao de conta do painel de administracao — liberar, recusar, desativar, reativar, encerrar sessoes e definir senha — alcancavel sem rolagem lateral em tela estreita, apresentando cada linha de tabela como um cartao com o rotulo da coluna junto de cada valor.
append-criterion [unverified] Em 390 px nenhuma aba do painel faz a pagina rolar de lado e todo botao de acao de conta esta dentro da largura da tela; em 1440 px as tabelas seguem tabelas com cabecalho — verified by `frontend/src/components/Admin.tsx` + `frontend/src/styles.css`.
bump-version minor
```
