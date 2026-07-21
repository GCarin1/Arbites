---
name: estado-ao-vivo-reconecta-no-remount
description: Estado ao vivo (stream SSE de um run, progresso) não pode viver só no componente que desmonta ao trocar de aba — o servidor guarda o buffer e faz replay, então a UI deve reconectar ao (re)montar para não "perder" o que estava acontecendo.
when: O agente vai criar/alterar uma tela que exibe um stream ao vivo (SSE/WebSocket) — terminal de run, progresso de tarefa — cujo componente desmonta ao navegar para outra aba/rota.
---

# Skill — estado-ao-vivo-reconecta-no-remount

## When to use this skill

- Vai mexer numa tela com `EventSource`/WebSocket cujo log/estado vive em
  `useState` local (ex.: `Automation.tsx`, terminal de run).
- Recebeu a queixa "saí da tela e voltei e perdi o que estava rodando / o
  terminal sumiu".

## Procedure

1. **Garanta o replay no servidor.** O produtor do stream deve manter um
   buffer (`run.log`) e, no endpoint (`GET /runs/{id}/stream`), **reenviar o
   buffer** para qualquer assinante que chega tarde — inclusive runs já
   terminados ainda em memória.
2. **Extraia a assinatura num helper reusável** (`attachStream(id)`) usado
   tanto pelo disparo quanto pela reconexão — sem duplicar o handler de
   `message`/`done`.
3. **Reconecte no mount.** Num `useEffect` de montagem, consulte o estado
   ativo (`GET /runs/active`) e, havendo run, restaure o objeto de run e
   chame `attachStream` — o replay repovoa o terminal.
4. **Evite toasts espúrios na reconexão.** O `attachStream` recebe um flag
   `toastOnDone`: `true` no disparo, `false` na reconexão (senão um run já
   concluído dispara um toast ao reconectar).

## Anti-patterns

- Manter o log só em `useState` do componente e não reconectar no mount —
  trocar de aba desmonta o componente, fecha o `EventSource` e o usuário
  "perde" o run que continua vivo no servidor. Foi um bug do change 0099.
- Reabrir o stream duplicando o handler em cada call-site (drift entre o
  fluxo de disparo e o de reconexão).

## Related material

- `frontend/src/components/Automation.tsx` — `attachStream`, efeito de
  reconexão, `startRun`.
- `backend/arbites/api.py` — `GET /runs/{id}/stream` (replay do buffer).
