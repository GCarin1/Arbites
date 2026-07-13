# Tasks — Change 0065-tela-de-automacao-como-centro-operacional-nao

- [ ] Reorganizar `Automation.tsx` em 3 abas: Configurar / Executar /
      Histórico (estado de aba local, sem rota nova).
- [ ] Aba Configurar: targets + editor .env + token GitHub + catálogo de
      variáveis (mover o que já existe, sem mudar comportamento).
- [ ] Aba Executar: disparo local (feature/tag) + disparo GitHub + terminal
      ao vivo (mover o que já existe).
- [ ] Aba Histórico: listar runs recentes (`origin != manual`) com
      status/duração/origem + resumo (tempo médio, falhas, última execução)
      via agregado reutilizando `automation_report` COM
      `ci_monitoring.name_pattern` (skill
      novo-consumidor-repassa-config-do-helper).
- [ ] Empty state instrutivo por aba (sem target / sem run).
- [ ] Suíte completa verde + `npm run build` limpo + smoke test.
- [ ] Atualizar spec local-automation: critérios novos → verified; bump
      minor.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0065-tela-de-automacao-como-centro-operacional-nao/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
