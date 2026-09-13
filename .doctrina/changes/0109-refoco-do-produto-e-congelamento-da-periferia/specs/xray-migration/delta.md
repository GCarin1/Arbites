# Spec Delta — capability: xray-migration

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/xray-migration/spec.md`

---

Congelada pela ADR 0012 — importação do Xray — a janela de migração cumpriu seu papel.

Congelado não é removido: o código permanece, as rotas continuam
respondendo, os testes continuam no gate e o dado de quem já usou não é
tocado. O que muda é que a capability sai da navegação principal e deixa de
receber investimento. Descongelar é outro ADR.

```ops
set-header Status: deprecated
set-header Implementation: verified — congelada pela ADR 0012: continua funcionando e no gate, fora do escopo ativo
```
