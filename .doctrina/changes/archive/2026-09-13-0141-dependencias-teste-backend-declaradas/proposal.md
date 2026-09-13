# Change 0141-dependencias-teste-backend-declaradas — dependencias de teste do backend nao declaradas: behave e um backend de keyring fazem parte do gate mas nao estao em nenhum requirements, entao um container novo reprova cinco testes

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** chore (confident; signals: dependencias) — opened as chore
- **Affects specs:** (none — chore)

## Why

dependencias de teste do backend nao declaradas: behave e um backend de keyring fazem parte do gate mas nao estao em nenhum requirements, entao um container novo reprova cinco testes

## What

`backend/requirements.txt` declara o que o Arbites precisa para RODAR. O que
ele precisa para ser TESTADO não está declarado em lugar nenhum:

- `pytest` — o runner do gate (`doctrina verify`).
- `behave` — os testes de `test_local_runs.py` rodam behave DE VERDADE, como
  o próprio docstring do arquivo diz ("behave REAL"). Sem ele, quatro testes
  reprovam.
- um backend de keyring (`keyrings.alt` serve) — `test_ai_optional.py` grava
  a chave do provider no keyring do SO (ADR 0008). Num container sem
  Secret Service, `keyring` cai no backend `fail` e levanta `NoKeyringError`.

Enquanto a máquina tem esses pacotes por acaso, o gate passa. Quando o
container é reciclado, `doctrina verify` reprova cinco testes que ninguém
mexeu — foi exatamente o que aconteceu nesta sessão, e o primeiro diagnóstico
plausível ("alguém quebrou o runner") é o errado.

Pior: a versão do `behave` não estava fixada. A que voltou no container novo
descarrega o stream mais cedo que a anterior, e isso DESTAPOU um defeito real
de cenário interrompido virando `passed` (change 0137). O defeito era nosso;
a suíte só tinha parado de ter sorte.

- `backend/requirements-dev.txt` (novo) — as dependências de teste, com a
  versão do `behave` fixada, e um comentário dizendo por que cada uma existe.
- `README.md` — o passo de instalação para quem vai rodar a suíte.

## Scope boundaries

- Não muda `requirements.txt`: nada disso é preciso para rodar o produto.
- Não cria CI — este repositório não tem workflow, e criar um é decisão de
  produto, não consequência desta lacuna.
- Não muda nenhum teste.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] Num ambiente limpo, `pip install -r backend/requirements.txt -r
      backend/requirements-dev.txt` é suficiente para a suíte passar inteira
      — conferido conferindo que os cinco testes que reprovavam por falta de
      pacote passam com o arquivo aplicado.
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
