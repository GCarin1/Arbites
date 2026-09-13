# Spec Delta — capability: risk-map

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/risk-map/spec.md`

---

Congelada pela ADR 0012 — mapa de risco.

Congelado não é removido: o código permanece, as rotas continuam
respondendo, os testes continuam no gate e o dado de quem já usou não é
tocado. O que muda é que a capability sai da navegação principal e deixa de
receber investimento. Descongelar é outro ADR.

```ops
set-header Status: deprecated
set-header Implementation: verified — congelada pela ADR 0012: continua funcionando e no gate, fora do escopo ativo
```
