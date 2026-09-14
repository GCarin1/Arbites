# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

```ops
append-requirement ubiquitous: The system shall apresentar acao de varias palavras como um controle unico e delimitado, e nao como texto solto, para que o rotulo nao seja lido como varias acoes distintas.
append-criterion [unverified] As acoes do sino tem contorno proprio e fonte proporcional, entao "Marcar todas como lidas" le como um botao e nao como quatro links — verified by `frontend/src/styles.css`.
bump-version patch
```
