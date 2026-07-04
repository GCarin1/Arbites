# Design — Change 0006-m4-github-actions-workflow-dispatch-com-correlac

## Approach

`ci.py` separa três coisas: (1) `GitHubClient` — interface fina sobre a
API REST do GitHub (dispatch, list/get runs, jobs, artifact zip) com
implementação httpx e backoff em 403/429; (2) `TokenStore` — wrapper do
`keyring` (service "arbites-github"), única fonte do PAT; (3) `CIManager`
— orquestração: cria a execution `github_actions`, correlaciona o run
(busca o run mais recente do workflow com `event=workflow_dispatch`
criado após o dispatch, janela de 30 s — a API não retorna o run id do
dispatch), expõe status consolidado e coleta o artifact ao `completed`.

A coleta abre o zip do artifact, acha o Cucumber JSON e reaproveita o
`behave_json` do M3 — resultado: execution estruturalmente idêntica à de
um run local (critério do milestone). Screenshots no artifact sob
`evidences/CT-XXXX/` viram evidências hasheadas.

O app injeta o client via `create_app(github_client=...)`: produção usa o
real; os testes passam um `FakeGitHub` em memória que simula dispatch →
run → jobs → artifact (zip real construído no teste). O gate não depende
de rede nem de segredo.

## Alternatives considered

- Testar contra a API real do GitHub — rejeitado no gate: exige rede,
  repo e PAT; o cliente real é deliberadamente fino (shapes fixados no
  fake).
- Logs ao vivo por step Gherkin — impossível (ADR 0006).

## Trade-offs and risks

- O fake pode divergir da API real — mitigado mantendo o client real
  trivial (um método ≈ um endpoint REST documentado) e o parse todo do
  lado testado.
- Correlação por janela de 30 s pode pegar run errado se dois dispatches
  simultâneos — aceito (single-user; documentado no spec).

## Decisions to record as ADRs

Nenhuma nova — executa ADRs 0006 e 0008.
