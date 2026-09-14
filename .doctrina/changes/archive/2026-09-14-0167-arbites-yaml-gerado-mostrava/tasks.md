# Tasks — Change 0167-arbites-yaml-gerado-mostrava

- [x] Os seis blocos que faltavam entram no default: `squads`, `audit`,
      `requirements`, `metric_thresholds`, `health_score`, `ci_monitoring`.
- [x] O arquivo passa a nascer de um template COMENTADO, não de um dump mudo.
- [x] O template avisa, nele mesmo, que segredo não entra ali e onde mora.
- [x] Teste que compara template e default — dois lugares que dizem a mesma
      coisa divergem sozinhos.
- [x] Teste que enumera as chaves lidas no código e exige que apareçam.
- [x] `.env.example` cobre o uso FORA do container, o token do GitHub e os
      opcionais, e avisa sobre a senha que não muda por lá.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-14-0167-arbites-yaml-gerado-mostrava/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
