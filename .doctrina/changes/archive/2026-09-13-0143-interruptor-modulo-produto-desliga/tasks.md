# Tasks — Change 0143-interruptor-modulo-produto-desliga

- [x] Registrar a decisão em ADR: o que é módulo, quais são as três camadas
      e por que o núcleo não é desligável.
- [x] Criar o registro `MODULES` (rótulo, aba, caminhos) e devolver
      `kind`/`tab` na listagem de interruptores.
- [x] Gerar as linhas de `_GOVERNED` a partir do registro, para o bloqueio
      do servidor e o que a UI esconde virem da mesma lista.
- [x] Fazer `isReachable` decidir o render além do menu, com tela própria
      para módulo desligado e sem piscar no primeiro carregamento.
- [x] Abrir o canal que faz a casca reler os interruptores quando o painel
      muda um.
- [x] Trocar a tabela de interruptores por lista de toggles, separada em
      módulos e superfícies.
- [x] Escrever os testes: módulo desligado recusa tudo que é dele e nada do
      núcleo; só admin liga/desliga; só admin gerencia cadastro.
- [x] Provar no navegador o ciclo desligar → religar nas três camadas.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0143-interruptor-modulo-produto-desliga/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
