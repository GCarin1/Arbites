# Tasks — Change 0135-barra-sub-abas-ia-transborda

- [x] Reproduzir em 390 px: abrir `#/ia` no navegador e registrar que a caixa
      da aba "Configuração" ultrapassa a borda direita da faixa e que a faixa
      não rola.
- [x] Criar `frontend/src/components/TabBar.tsx` — faixa canônica com
      `role="tablist"`, abas que não encolhem e a ativa trazida ao campo de
      visão na troca.
- [x] Dar rolagem horizontal e sombra de borda a `.tab-bar` em `styles.css`
      pela técnica `background-attachment: local/scroll`, sem JavaScript.
- [x] Trocar as duas faixas escritas à mão (`AiAssist.tsx`, `Automation.tsx`)
      pelo componente.
- [x] Medir de novo em 390 px e em 1440 px e guardar as capturas.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0135-barra-sub-abas-ia-transborda/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
