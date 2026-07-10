---
name: tela-preta-crash-de-render-sem-error-boundary
description: Uma aba/tela que fica "preta" (em branco) SEM erro nos logs de servidor é quase sempre um crash de render do React — o erro está no console do browser, e sem ErrorBoundary o React 18 desmonta o app inteiro. Gatilho comum front novo lê um campo que o backend não-reiniciado ainda não devolve (ex. [...data.campo] com campo undefined).
when: Ao investigar "tela preta"/tela em branco numa SPA que aparece só ao abrir uma aba específica, sem nada nos logs de back nem de front; ou ao adicionar um campo novo na resposta de um endpoint que o front passa a consumir.
---

# Skill — tela-preta-crash-de-render-sem-error-boundary

## When to use this skill

- Uma aba específica abre "preta"/em branco e **nada aparece nos logs** de
  backend nem do dev server. O resto do app parece ok até você clicar nela.
- Você acabou de adicionar um campo novo à resposta de um endpoint e o front
  passou a lê-lo.

## Diagnóstico (o que "tela preta sem log" quase sempre significa)

1. **É crash de render do React, não erro de servidor.** Erros de runtime do
   browser vão para o **console do DevTools**, nunca para os logs do uvicorn/
   vite. "Não tem nada no log" é a pista, não a ausência de bug.
2. **Sem ErrorBoundary, um throw no render desmonta a árvore inteira** (React
   18). Sobra o fundo do app — se o tema é escuro, parece "tela preta".
3. **Gatilho clássico: skew de versão front↔back.** O front novo lê um campo
   que o backend **não-reiniciado** ainda não devolve. A chamada retorna 200
   (o back não erra; params extras/desconhecidos costumam ser ignorados), mas
   o campo vem `undefined`. Aí `[...data.campo]`, `data.campo.map(...)` ou
   `Object.keys(data.campo)` estouram `TypeError` no render.

## Procedure

1. **Abra o console do browser** (F12) — o stack aponta o componente e a
   linha exatos. É a evidência que os logs de servidor nunca terão.
2. **Corrija o acesso frágil**: trate a resposta como possivelmente parcial.
   `data.campo ?? []`, `data.obj?.[k] ?? 0`, nunca espalhe/itere um campo que
   pode faltar (`[...data.campo]` só depois de garantir array).
3. **Adicione um ErrorBoundary** em volta do conteúdo principal (uma classe
   com `getDerivedStateFromError`), **keyado pela view** (`key={tab}`) para
   que trocar de aba limpe o erro. Assim UMA view nunca mais derruba o app —
   o pior caso vira uma mensagem, com menu e demais abas vivos.
4. **Confirme o gatilho de skew**: reiniciar o backend costuma "resolver"
   porque a resposta volta completa — mas o front tem que ser robusto de
   qualquer forma (o usuário nem sempre reinicia).

## Anti-patterns

- Procurar o bug nos logs do servidor quando o erro é do browser.
- Assumir que resposta 200 = resposta no shape esperado (versão pode divergir).
- Espalhar/iterar um campo novo do backend sem guardá-lo — quebra contra
  qualquer resposta antiga/parcial.
- App inteiro sem nenhum ErrorBoundary — qualquer crash de view = app morto
  e silencioso.

## Related material

- `frontend/src/components/ErrorBoundary.tsx` — boundary reutilizável.
- `frontend/src/App.tsx` — `<ErrorBoundary key={tab}>`.
- `frontend/src/components/ActivityHeatmap.tsx` — `data.years ?? []` (o campo
  que faltava na resposta do backend não-reiniciado).
