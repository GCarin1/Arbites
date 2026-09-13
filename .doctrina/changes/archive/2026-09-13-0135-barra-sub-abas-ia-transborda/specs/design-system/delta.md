# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

```ops
append-requirement ubiquitous: The system shall dar rolagem horizontal a uma faixa de abas que nao cabe na largura disponivel, com sinal visivel do lado que ainda esconde aba e a aba ativa trazida ao campo de visao na troca, em vez de cortar a ultima aba na borda do quadro.
append-criterion [unverified] Em 390 px a faixa de abas da tela de IA rola dentro de si — a caixa da aba "Configuracao" fica inteira apos rolar e a faixa exibe sombra no lado com aba escondida — e em 1440 px a mesma faixa nao rola nem exibe sombra — verified by `frontend/src/components/TabBar.tsx` + `frontend/src/styles.css`.
bump-version minor
```
