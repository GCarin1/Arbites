# Delta — ai-assist (change 0078)

**Operation:** MODIFIED

Reformulação da aba de IA: sub-abas + provider global. UI apenas; sem
mudança de contrato de backend. O conteúdo já foi mesclado direto em
`.doctrina/specs/ai-assist/spec.md` (deltas prose, merge manual).

## MODIFIED — Requirements (EARS)

### State-driven (substituir a regra "área de IA abre na visão de trabalho…")

- While a área de IA está aberta, the system shall organizá-la em sub-abas
  internas **Gerar · Revisar · Context Pack · Configuração**, abrindo em
  Gerar (trabalho), com o contexto ativo e o histórico de interações de IA
  (agent_events via `GET /memory/timeline?kinds=agent`) acompanhando as abas
  de trabalho; a configuração de providers vive na sub-aba Configuração
  (não mais um card colapsado atrás de um toggle). [unverified]
- While a área de IA está aberta, the system shall oferecer um seletor de
  provider ÚNICO no cabeçalho da tela, usado por Gerar, Revisar e Casos
  negativos — sem repetir o dropdown de provider por card. [unverified]

## Acceptance criteria (replace criterion 12)

12. [unverified] A área de IA abre na sub-aba Gerar, alterna entre
    Gerar/Revisar/Context Pack/Configuração, com o contexto ativo e o
    histórico visíveis no trabalho e a config de providers na sua sub-aba; o
    provider escolhido no cabeçalho vale para gerar/revisar/negativos; o
    preview segue sinalizando "nada gravado, aceite item a item" — verified
    by build + smoke dos endpoints consumidos (`/ai/providers`, `/profile`,
    `/decisions?status=accepted`, `/defects?has_lesson=true`,
    `/memory/timeline?kinds=agent`) + revisão visual.
