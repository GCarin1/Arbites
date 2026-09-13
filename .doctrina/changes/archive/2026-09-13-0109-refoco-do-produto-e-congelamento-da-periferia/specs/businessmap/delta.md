# Spec Delta — capability: businessmap

**Operation:** REMOVED
**Target spec on apply:** `.doctrina/specs/businessmap/spec.md`

---

Enterrada pela ADR 0012. Diferente das oito capabilities congeladas, esta
nunca saiu de `Implementation: planned` — não há código, rota nem dado para
preservar, só uma intenção de 2026-07 condicionada a uma migração
corporativa que não se concretizou.

Manter uma spec `active` de algo que nunca foi construído é a pior forma de
dívida documental: ela aparece na contagem de capabilities, é lida como
compromisso vivo e não custa nada a ninguém removê-la.

O vínculo com o sistema corporativo de gestão continua existindo pelo campo
`external_key`, que já é a forma como requisitos e defeitos apontam para
fora. SC10 sai do `product.md` junto.
