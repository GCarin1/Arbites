# Tasks — Change 0049 (chore / bugfix)

- [x] Diagnóstico: crash de render (não de servidor) → console do browser, não logs; fundo escuro = "tela preta".
- [x] Causa: `[...data.years]` com `years` ausente (resposta do backend não-reiniciado, shape 0047) → TypeError.
- [x] Fix pontual: `data.years ?? []` (e `data.totals?.[metric] ?? 0`) no ActivityHeatmap.
- [x] Fix sistêmico: `ErrorBoundary` novo, envolvendo o conteúdo principal em App, keyado por `tab`
      (trocar de aba limpa o erro). Uma view não derruba mais o app inteiro.
- [x] Build verde; causa-raiz demonstrada (resposta sem `years` → crash; com `?? []` → ok).

## Closing steps

- [x] Apply (chore, zero deltas).
- [x] Archive.
- [x] Update index.json.
