# Change 0189-cenarios-resultado-vazio-porque — cenário reconhecido pela forma, não pelo nome

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

45 execuções ingeridas, 54 anexos numa delas, acessibilidade trazendo 1367
achados — e a pizza "Cenários por resultado" vazia.

Não faltava dado. O relatório Cucumber só era reconhecido se o arquivo
terminasse **exatamente** em `cucumber.json` ou `result.json`. Um
`cucumber-report.json`, um `results.json` no plural, um `report-trader.json`
— nenhum casava, e a extração de cenários recebia lista vazia sem dizer nada.

Reconhecer por nome nunca ia funcionar: cada pipeline nomeia do seu jeito, e
a lista de nomes prováveis não termina. A FORMA, sim, está no padrão: uma
lista de features, cada uma com `elements`. Reconhecê-la não é inferir
semântica — é ler um formato documentado, como o relatório do axe-core já
era lido.

## What

- `ci_ingest.e_relatorio_cucumber()`: reconhecimento pela forma, com corte
  barato antes de desserializar (não começa com `[`, ou passa do limite de
  tamanho, nem é aberto).
- `extrair_cenarios()` e `_por_convencao()` passam a usá-la. A entrada
  `cucumber` da tabela de nomes **sai**: um `result.json` que não é uma lista
  de features não é um relatório, e dizer que é seria trocar um silêncio por
  uma mentira.
- `ci_ingest.reprocessar()` e `POST /ci/reprocess`: relê os anexos que **já
  estão no disco** e refaz só o que é derivado deles. Sem rede.
- Aba Configuração ganha o botão **Reprocessar do disco**.

## Scope boundaries

O manifesto declarado continua vencendo a forma (ADR 0016): a forma é o
fallback, não a regra. Sinais continuam saindo só do manifesto — um número
solto num arquivo desconhecido não tem nome nem unidade, e inventar os dois
seria pior que não ter. O reprocessamento não toca no que veio do provedor.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_cenarios_por_forma.py`: 22 testes, incluindo cinco
      nomes de arquivo que antes falhavam, o JSON que não é Cucumber, o
      arquivo grande demais, e o reprocessamento idempotente.

## Open questions

Nenhuma.
