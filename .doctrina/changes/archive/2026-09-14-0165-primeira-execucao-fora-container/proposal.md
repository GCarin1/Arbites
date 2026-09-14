# Change 0165-primeira-execucao-fora-container — primeira execucao fora do container: o .env nunca era lido, entao nenhum admin era criado e a pessoa se trancava fora por tentativas

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** auth

## Why

primeira execucao fora do container: o .env nunca era lido, entao nenhum admin era criado e a pessoa se trancava fora por tentativas

## What

**Dois sintomas, uma causa.** Numa máquina sem Docker, `npm build` +
`python -m arbites serve`: o `.env` não era lido e, logo depois, a pessoa era
bloqueada por tentativas de login.

A causa: **quem lê o `.env` no Docker é o Compose, não o Arbites.** É recurso
do Compose. Quem sobe em container vê as variáveis chegarem e conclui, com
toda a razão, que o produto lê o arquivo. Fora do container, nada lia.

A cadeia inteira:

1. `.env` ignorado → `ARBITES_ADMIN_EMAIL` e `ARBITES_ADMIN_PASSWORD` vazias;
2. `bootstrap_admin` não cria conta nenhuma e **retorna em silêncio**;
3. a instância sobe **sem conta alguma** e parece normal;
4. a pessoa tenta entrar numa conta que nunca existiu;
5. cinco falhas depois, bloqueio por tentativas — **sem saída documentada**.

Três correções, uma por elo:

- **Ler o `.env`** do diretório de execução, com o ambiente do processo tendo
  precedência (mesma regra do Compose e da ADR 0017). O log mostra as CHAVES
  aplicadas, nunca os valores — este arquivo costuma ter senha dentro.
- **Dar voz ao arranque impossível**: sem admin e sem credencial, o log diz
  que ninguém vai conseguir entrar e nomeia as variáveis. Um arranque que não
  pode dar certo precisa dizer isso.
- **Uma saída do bloqueio**: `python -m arbites unlock`. Quem roda isso está
  com o arquivo do banco na mão — já podia apagar o banco inteiro. O que não
  pode existir é ficar trancado fora da própria máquina sem saída.

## Scope boundaries

- Não afrouxa o bloqueio: continuam cinco tentativas em quinze minutos. O que
  muda é existir uma saída local, não a regra.
- Não muda a ADR 0008: `.env` está no `.gitignore` e não é o workspace. Em
  container o token já vinha dele, pelas mãos do Compose.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] O `.env` é aplicado, e variável já exportada não é sobreposta.
- [x] Os valores nunca saem no log — só os nomes das variáveis.
- [x] Arranque sem admin e sem credencial registra erro nomeando as
      variáveis e o arquivo.
- [x] `unlock` libera o login, e `--email` alcança uma conta só.

## Open questions

**A lição, e ela já apareceu antes nesta sessão:** o defeito não estava no
código que falhou — estava na DIFERENÇA entre dois ambientes de execução. Foi
exatamente assim com o keyring (change 0160): a suíte rodava com um backend
instalado e nunca via o que o container via. Aqui, os testes definem o
ambiente na mão e nunca viram o que uma máquina limpa vê.

Vale como padrão: quando um caminho de instalação depende de algo que o
ambiente de teste fornece de graça, esse algo precisa de um teste que simule
a ausência dele.

<!-- List unresolved decisions. Empty if none. -->
