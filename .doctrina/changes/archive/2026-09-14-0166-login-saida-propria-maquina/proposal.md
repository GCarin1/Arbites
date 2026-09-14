# Change 0166-login-saida-propria-maquina — 401 no login sem saida na propria maquina: conta inexistente senha errada e conta inativa respondem igual e nao havia como diagnosticar nem redefinir

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** runtime (uncertain; signals: diagnosticar) — opened anyway (--force)
- **Affects specs:** auth

## Why

401 no login sem saida na propria maquina: conta inexistente senha errada e conta inativa respondem igual e nao havia como diagnosticar nem redefinir

## What

O login responde **401 "e-mail ou senha inválidos"** para TRÊS situações
diferentes: conta inexistente, senha errada e conta não-ativa. Isso é
deliberado e continua certo — distinguir "não existe" de "senha errada"
entrega uma lista de contas válidas a quem tenta adivinhar.

Mas de dentro da própria máquina isso vira um mistério **sem saída**. A pessoa
tem o arquivo do banco na mão e mesmo assim não consegue descobrir se o
problema é a senha ou a ausência de conta.

E há um caminho especialmente traiçoeiro: **se a conta já existe, o bootstrap
por ambiente nunca mais toca nela** (`bootstrap_admin` desiste quando há admin
ativo, e quando promove um usuário existente NÃO mexe na senha). Trocar
`ARBITES_ADMIN_PASSWORD` no `.env` não muda a senha de uma conta criada antes
— e a pessoa fica editando um arquivo que não tem efeito nenhum, convencida de
que o produto não está lendo.

`python -m arbites admin`:

- **sem argumentos**, diz o que existe — contas, papel, status — ou avisa que
  não existe conta alguma, que é o motivo mais comum do 401 numa instalação
  nova;
- **com `--email` e `--password`**, cria ou redefine: define a senha, reativa
  e promove a admin, e **destrava o bloqueio junto** (quem chegou aqui
  provavelmente errou a senha algumas vezes — exigir um segundo comando seria
  pedir o óbvio).

A saída nunca mostra senha nem hash, e a conta nasce com troca obrigatória: a
senha passou pelo histórico do shell, então serve para entrar uma vez.

## Scope boundaries

- Não afrouxa a resposta da API: o 401 continua indistinguível de fora. O que
  muda é existir resposta de DENTRO da máquina.
- Não cria recuperação por e-mail: o produto é local e não envia nada.

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
- [x] Workspace sem conta explica o 401 e ensina o comando que resolve.
- [x] Criar a primeira conta permite entrar.
- [x] Redefinir a senha de quem já existe permite entrar, e a antiga para de
      funcionar.
- [x] Conta pendente volta a ativa e entra.
- [x] Senha curta é recusada sem tocar na conta existente.
- [x] Redefinir destrava o bloqueio por tentativas.
- [x] A listagem nunca mostra senha nem hash.

## Open questions

**Por que isto não apareceu antes:** toda a suíte cria contas pelo fluxo
interno, com a senha em mãos. Nenhum teste vivia a situação de "tenho o banco
e não sei a senha" — que é a situação normal de quem instala numa máquina
nova, erra uma vez e recomeça.

É a terceira vez nesta sessão que o defeito está na DIFERENÇA entre o ambiente
de teste e o real (keyring no container, `.env` fora do Compose, e agora
credencial que o teste sempre conhece). Vale como padrão, e não como
coincidência.

<!-- List unresolved decisions. Empty if none. -->
