# Change 0191-taxa-sucesso-falhas-contando — cancelada não é falha

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

O painel mostrava **55.6% de sucesso** em 45 execuções. A conta estava certa
e a pergunta, errada: das 45, **12 foram canceladas e 1 pulada**. Nenhuma das
13 disse nada sobre o produto — alguém apertou o botão, ou um push novo
substituiu a fila, ou uma condição do workflow não bateu.

A verdade era 25 de 32: **78.1%**. E a tabela por repositório dizia "20
falhas" onde havia 7, porque somava tudo que não passou.

A diferença entre 55% e 78% é a diferença entre uma suíte que parece quebrada
e uma que parece saudável — e é olhando para esse número que alguém decide
onde investir a semana.

## What

- `ci_ingest.e_conclusiva()` e `taxa_de_sucesso()`: a conta num lugar só,
  devolvendo taxa, denominador e quantas ficaram de fora.
- `painel()`, `_recorte()` e `distribuicao()` passam a usá-la. `timed_out`
  fica **dentro** das conclusivas: estourar o tempo é falhar com um motivo.
- `failures` por recorte deixa de ser "tudo que não passou".
- A pizza "Execuções por resultado" mostra o veredito; cancelada e pulada
  viram um rodapé nomeado. O card da taxa mostra o denominador.
- Um período em que nada deu veredito responde **—**, nunca 0%.

## Scope boundaries

O total de execuções continua sendo o total de verdade — nada é escondido,
só sai do denominador. A retenção, a ingestão e os sinais não mudam.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_execucao_conclusiva.py`: 14 testes, incluindo o
      caso exato do relatório (25 verdes, 7 falhas, 12 canceladas, 1 pulada →
      78.1% sobre 32) e o período só de canceladas.

## Open questions

Nenhuma.
