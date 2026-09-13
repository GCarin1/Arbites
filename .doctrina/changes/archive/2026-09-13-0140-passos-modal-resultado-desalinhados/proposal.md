# Change 0140-passos-modal-resultado-desalinhados — passos do modal de resultado desalinhados em 390px: o texto do passo espremido em tres linhas ao lado dos botoes e o status solto na linha seguinte, e o envio de evidencia mostra o input de arquivo cru do sistema

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

passos do modal de resultado desalinhados em 390px: o texto do passo espremido em tres linhas ao lado dos botoes e o status solto na linha seguinte, e o envio de evidencia mostra o input de arquivo cru do sistema

## What

Duas coisas na mesma tela, as duas do sistema visual:

**1. A linha do passo.** `.step-row` é um flex de uma linha com o texto em
`flex: 1` inline. Em 390 px o texto encolhe até uma coluna de ~90 px e
"Abrir a tela de login" vira três linhas empilhadas ao lado de `pass fail
block`, enquanto o status (`pending`) cai para uma quarta linha, órfão, sem
nada dizendo a que passo pertence. Medido: 4 alturas distintas numa linha de
104 px. O passo é o que se lê para executar o teste — ele é o conteúdo, os
botões são a ação sobre ele.

Em tela estreita a linha passa a ter duas faixas explícitas: número + texto
do passo em cima, ações + status embaixo. O status cola nos botões que o
mudam, que é onde ele significa alguma coisa.

**2. O envio de evidência.** O `input[type=file]` nativo aparece cru — a
caixa "Choose File / No file chosen" com a fonte e a cor do sistema
operacional, em inglês, no meio de um formulário em português. O perfil já
resolvia isso desde a change de avatar, escondendo o input e clicando nele
por um botão de verdade; aqui esse padrão vira componente (`FilePicker`) e
passa a valer nos quatro lugares que enviam arquivo: evidência de resultado,
import de CTs por IA, import do Xray e a foto do perfil.

- `frontend/src/components/FilePicker.tsx` (novo)
- `frontend/src/components/Executions.tsx` — passo com classe própria
  (`step-text`) em vez de `style` inline, e o envio pelo componente.
- `frontend/src/components/TcRepository.tsx`, `XrayImport.tsx`,
  `Profile.tsx` — passam a usar o mesmo componente.
- `frontend/src/styles.css` — a faixa do passo em tela estreita e
  `.file-picker`.

**Afeta spec:** `design-system` — escolher arquivo é um controle canônico
como botão, input e card, e não tinha regra; a linha de passo também não.

## Scope boundaries

- Não muda o que o passo faz, nem a máquina de status do resultado.
- Não muda o formato nem o limite dos arquivos aceitos em nenhum dos quatro
  pontos de envio.
- Não mexe no cabeçalho da execução (change 0139) nem no quadro.

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
- [x] Em 390 px, na linha do passo, o texto do passo e o número ficam numa
      faixa e as ações com o status na faixa seguinte — o status nunca
      sozinho numa terceira.
- [x] Em 390 px nenhuma tela mostra `input[type=file]` visível: os quatro
      pontos de envio passam pelo botão do sistema.
- [x] O arquivo escolhido tem o nome mostrado, e escolher DE NOVO o mesmo
      arquivo dispara o envio outra vez.
- [x] Em 1440 px a linha do passo continua numa faixa só.

## Open questions

Nenhuma.
