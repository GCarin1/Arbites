---
name: mesmo-componente-em-dois-ramos-mantem-estado
description: Dois ramos de um `if` que renderizam o MESMO componente na mesma posição fazem o React reaproveitar a instância — o `useState` inicial não roda de novo e o componente aparece com o estado do ramo anterior; a saída é uma `key` distinta por ramo.
when: O agente vai escrever, ler ou depurar um componente React que renderiza o mesmo elemento em mais de um ramo de condicional, com props que decidem o estado INICIAL (modo, aba, passo de wizard, formulário pré-preenchido).
---

# Skill — mesmo componente em dois ramos mantém o estado

## When to use this skill

- Um componente-porteiro escolhe entre fases (`checking` / `anonymous` /
  `must-change` / `authenticated`) e mais de uma fase renderiza o mesmo
  componente filho.
- Uma prop como `forcePasswordChange`, `modoInicial`, `abaInicial` alimenta um
  `useState(<prop> ? A : B)` no filho.
- O sintoma relatado é "a tela não muda", "cliquei e não aconteceu nada",
  "voltou para a mesma tela como se o login não tivesse acontecido".

## Procedure

1. Localize os ramos que renderizam o mesmo tipo de elemento na mesma posição
   da árvore. É a posição que importa, não o arquivo.
2. Confira se o filho tem `useState(prop ? X : Y)`. Se tiver, o valor inicial
   **só vale na primeira montagem** — trocar de ramo não remonta nada.
3. Dê uma `key` distinta e estável a cada ramo (`key="anonymous"`,
   `key="must-change"`). A `key` diferente força desmontar e montar de novo,
   e aí o `useState` inicial roda com a prop nova.
4. Alternativa quando remontar custa caro (perderia dados digitados): não use
   `key`; sincronize com `useEffect` sobre a prop, de propósito e comentado.
5. Confira também os **callbacks** de cada ramo. Um ramo costuma assumir que
   só pode ser chamado por um caminho (`onAuthenticated` no ramo da troca de
   senha "só pode vir de uma troca bem-sucedida"); quando o estado vaza entre
   ramos, essa suposição vira um bug pior que o primeiro.
6. Prove no navegador, não no código: dirija o fluxo real duas vezes seguidas
   e confira o título/os campos da tela em cada volta.

## Anti-patterns

- Confiar que `useState(prop ? A : B)` "reage" à prop. Ele não reage nunca.
- Callback de ramo que decreta o estado final (`setState({phase:
  "authenticated", user})`) em vez de derivá-lo do dado (`user.must_change_password
  ? ... : ...`). Se o ramo for alcançado por um caminho não previsto, o decreto
  põe a aplicação num estado impossível — e, quando o backend recusa, ela fica
  presa sem saída.
- Fechar o diagnóstico na primeira tentativa do fluxo. O defeito da change 0169
  só apareceu na SEGUNDA vez que a pessoa clicou em "Entrar".

## Related material

- `.doctrina/changes/archive/2026-09-15-0169-tela-troca-senha-obrigatoria/` —
  onde isto custou uma sessão presa com 403 em todas as rotas.
- `frontend/src/components/AuthGate.tsx` — as duas `key` e o callback honesto.
- [Workflow](../../docs/en/workflow.md)
