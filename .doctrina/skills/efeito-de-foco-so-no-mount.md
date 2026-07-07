---
name: efeito-de-foco-so-no-mount
description: Efeitos de foco/scroll-lock (modais, autofocus) devem rodar só no mount — callbacks instáveis nas deps re-disparam o efeito e roubam o cursor.
when: Ao criar/editar um componente React com foco automático, trap de foco, scroll-lock ou qualquer useEffect que "faça algo uma vez" e que dependa de props de callback (onClose/onChange).
---

# Skill — efeito-de-foco-so-no-mount

## When to use this skill

- Está mexendo em `Modal.tsx` ou em qualquer componente que dá foco inicial
  a um campo (`initialFocus`, autofocus) ou trava o scroll do body.
- Um bug relata "o cursor pula para outro campo enquanto eu digito", "o modal
  re-foca sozinho", "o scroll trava/destrava piscando".
- Vai colocar `onClose`, `onChange`, `onSaved` (callbacks vindos do pai) nas
  dependências de um `useEffect` que deveria rodar uma vez.

## O bug (real, change 0019)

O `Modal` focava o `initialFocus` num `useEffect` com deps
`[onClose, initialFocus]`. Os pais passam `onClose={() => setX(null)}` — uma
**nova identidade a cada render**. E o `App` re-renderiza a árvore a cada 5s
(`setInterval(refresh, 5000)`). A cada re-render: cleanup do efeito (devolve o
foco ao elemento anterior) → efeito roda de novo (foca o `initialFocus` = o
título). Resultado: digitando no campo "squad", o cursor **pulava de volta
para o título**.

## Procedure

1. Efeito que deve acontecer **uma vez** (foco inicial, scroll-lock, medir DOM):
   deps `[]`. Capturar `initialFocus`/refs uma vez é intencional — silencie o
   lint com `// eslint-disable-next-line react-hooks/exhaustive-deps`.
2. Precisa do valor **atual** de um callback dentro de um listener (ex.: Esc →
   `onClose`) sem re-rodar o efeito? Leia por **ref**:
   ```tsx
   const onCloseRef = useRef(onClose);
   onCloseRef.current = onClose;              // atualiza a cada render
   useEffect(() => {
     const onKey = (e) => { if (e.key === "Escape") onCloseRef.current(); };
     document.addEventListener("keydown", onKey);
     return () => document.removeEventListener("keydown", onKey);
   }, []);                                     // registra uma vez
   ```
3. Separe os efeitos por ciclo de vida: um para "mount only" (foco/scroll),
   outro para listeners. Não misture algo que roda-uma-vez com deps que mudam.
4. Verifique com um pai que re-renderiza sozinho (o `App` já faz isso a cada
   5s): abrir o modal, digitar num campo != o inicial e esperar — o foco não
   pode voltar.

## Anti-patterns

- `useEffect(() => { target.focus(); ... }, [onClose])` — `onClose` recriado no
  pai re-foca o campo. Idem para qualquer callback/objeto/array inline nas deps.
- "Consertar" pondo `useCallback` no pai só esconde o problema — o efeito de
  foco ainda não deveria depender do callback.
- Trap de foco que re-executa a cada render em vez de gerenciar mount/unmount.

## Related material

- `frontend/src/components/Modal.tsx` — foco/scroll-lock no mount, Esc por ref.
- Change `0019` (arquivada) — o fix e o diagnóstico completo.
