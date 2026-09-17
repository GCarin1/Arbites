# Change 0192-limpar-toda-observabilidade-confirmacao — limpar tudo, com o tamanho do estrago na frente

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

Faltava um jeito de recomeçar. A retenção remove por idade, e não havia nada
que zerasse a observabilidade inteira — o que é justamente o que se quer
depois de ingerir com um reconhecimento errado, ou ao trocar de repositório
de origem.

"Limpar tudo" é a operação em que o produto mais precisa ser confiável: quem
a usa costuma estar irritado com um dado errado, e é exatamente aí que se
apaga o que não devia.

## What

- `ci_retencao.previa_total()` e `GET /ci/purge/preview`: quantas execuções,
  quantos anexos, quanto espaço e de que data a que data — **antes** de
  qualquer confirmação. Uma confirmação que não diz o tamanho não é
  confirmação, é um obstáculo.
- `ci_retencao.limpar_tudo()` e `POST /ci/purge` (privativo do admin, mesmo
  alcance da limpeza por retenção). Vai para a **lixeira**, como todo o resto
  do Arbites.
- A cobertura de busca (change 0190) é esquecida junto: mantê-la afirmaria
  que o período já foi varrido quando não há mais nada dele no disco, e a
  próxima busca não traria nada de volta.
- Aba Configuração: cartão com o botão e o `ConfirmModal` que já existe.

## Scope boundaries

As origens declaradas ficam: o que some é o dado, não a configuração —
limpar para reconferir e perder as origens obrigaria a reconfigurar tudo.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_limpar_observabilidade.py`: 9 testes, incluindo a
      prévia que não apaga, a lixeira, a cobertura esquecida junto, as
      origens preservadas e a recusa para quem não é admin.
- [x] Verificado no navegador com 45 execuções semeadas: o modal mostra 45
      execuções, 90 anexos, 0.1 MB e o intervalo de datas.

## Open questions

Nenhuma.
